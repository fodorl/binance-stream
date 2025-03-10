#!/usr/bin/env python3
"""
WebSocket client module for the Binance BBO stream application.
"""
import logging
import asyncio
import websockets
import ssl
import json
import traceback
import time
import socket
import requests
from config import WEBSOCKET_BASE_URL, INITIAL_BACKOFF, EXTENDED_BACKOFF_THRESHOLD, CONNECTION_TIMEOUT, DNS_TIMEOUT

logger = logging.getLogger(__name__)

# Try to import aiohttp, but don't fail if it's not available
try:
    import aiohttp
    import aiohttp.resolver
    AIOHTTP_AVAILABLE = True
    logger.info("aiohttp is available and will be used for improved connections")
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.info("aiohttp is not available, falling back to standard websockets")

# Try to import dnspython for custom DNS resolution
try:
    import dns.resolver
    DNSPYTHON_AVAILABLE = True
    logger.info("dnspython is available and will be used for custom DNS resolution")
except ImportError:
    DNSPYTHON_AVAILABLE = False
    logger.info("dnspython is not available, falling back to system DNS")

def resolve_with_custom_dns(hostname, port=None, family=socket.AF_INET):
    """
    Custom DNS resolution function using Google DNS servers (8.8.8.8, 8.8.4.4)
    """
    if DNSPYTHON_AVAILABLE:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8', '8.8.4.4']
            resolver.timeout = DNS_TIMEOUT
            resolver.lifetime = DNS_TIMEOUT
            
            answer = resolver.resolve(hostname, 'A')
            ip_address = answer[0].address
            logger.info(f"Resolved {hostname} to {ip_address} using custom DNS resolver")
            
            if port:
                return [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip_address, port))]
            else:
                return [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip_address, 0))]
        except Exception as e:
            logger.error(f"Custom DNS resolution failed: {e}")
            # Fall back to standard resolution
            return socket.getaddrinfo(hostname, port, family=family, type=socket.SOCK_STREAM)
    else:
        # Use standard resolution
        return socket.getaddrinfo(hostname, port, family=family, type=socket.SOCK_STREAM)

class BinanceWebSocketClient:
    def __init__(self, symbol, message_processor=None, auto_reconnect=True, max_retries=10):
        self.symbol = symbol.lower()
        self.message_processor = message_processor
        self.auto_reconnect = auto_reconnect
        self.max_retries = max_retries
        self.websocket = None
        self.retry_count = 0
        self.backoff_time = INITIAL_BACKOFF
        self.url = f"{WEBSOCKET_BASE_URL}/{self.symbol}@bookTicker"
        self.connection_active = False
        self.last_connection_attempt = 0
        self.connection_diagnostics_done = False

    async def perform_connection_diagnostics(self):
        """Perform network diagnostics to help troubleshoot connection issues"""
        if self.connection_diagnostics_done:
            return
            
        logger.info("Performing connection diagnostics...")
        
        # Parse URL to get host and port
        try:
            import urllib.parse
            parsed_url = urllib.parse.urlparse(self.url)
            host = parsed_url.netloc.split(':')[0]
            port = 443 if parsed_url.scheme == 'wss' else 80
            if ':' in parsed_url.netloc:
                port = int(parsed_url.netloc.split(':')[1])
            
            logger.info(f"WebSocket URL components: Host={host}, Port={port}, Path={parsed_url.path}")
            
            # DNS resolution test
            try:
                # First try custom DNS resolution with Google DNS
                try:
                    custom_addrinfo = resolve_with_custom_dns(host, port)
                    for family, socktype, proto, canonname, sockaddr in custom_addrinfo:
                        ip, port = sockaddr
                        logger.info(f"Custom DNS resolved {host} to {ip}:{port}")
                    
                    # Try a direct TCP connection with custom DNS
                    ip = custom_addrinfo[0][4][0]  # Extract IP from first addrinfo entry
                    start_time = time.time()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5.0)
                    s.connect((ip, port))
                    s.close()
                    tcp_time = time.time() - start_time
                    logger.info(f"TCP connection to {ip}:{port} successful (took {tcp_time:.3f}s)")
                    
                except Exception as custom_dns_error:
                    logger.error(f"Custom DNS resolution failed: {custom_dns_error}")
                    
                    # Fall back to system DNS
                    start_time = time.time()
                    addrinfo = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
                    dns_time = time.time() - start_time
                    
                    for family, socktype, proto, canonname, sockaddr in addrinfo:
                        ip, port = sockaddr
                        logger.info(f"System DNS resolved {host} to {ip}:{port} (took {dns_time:.3f}s)")
                    
                    # Try a direct TCP connection to test reachability
                    start_time = time.time()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5.0)
                    s.connect((ip, port))
                    s.close()
                    tcp_time = time.time() - start_time
                    logger.info(f"TCP connection to {ip}:{port} successful (took {tcp_time:.3f}s)")
                
            except socket.gaierror as e:
                logger.error(f"DNS resolution failed: {e}")
            except socket.timeout:
                logger.error(f"TCP connection timed out to {host}:{port}")
            except Exception as e:
                logger.error(f"Network diagnostic error: {e}")
            
            # Try HTTP connection to API endpoint to check general connectivity
            try:
                start_time = time.time()
                # Use a hardcoded IP address for api.binance.com if we can't resolve it
                api_endpoint = f"https://{host}/api/v3/ping" if 'stream.binance.com' in host else f"https://api.binance.com/api/v3/ping"
                
                # Try to use custom resolver for HTTP connection
                if AIOHTTP_AVAILABLE:
                    resolver = aiohttp.resolver.AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"])
                    timeout = aiohttp.ClientTimeout(total=CONNECTION_TIMEOUT)
                    connector = aiohttp.TCPConnector(resolver=resolver, ssl=False)
                    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                        async with session.get(api_endpoint) as response:
                            http_time = time.time() - start_time
                            logger.info(f"HTTP connection to {api_endpoint} returned status {response.status} (took {http_time:.3f}s)")
                else:
                    # Fall back to requests
                    response = requests.get(api_endpoint, timeout=5)
                    http_time = time.time() - start_time
                    logger.info(f"HTTP connection to {api_endpoint} returned status {response.status_code} (took {http_time:.3f}s)")
                    
            except Exception as e:
                logger.error(f"HTTP connection to Binance API failed: {e}")
                
        except Exception as e:
            logger.error(f"Error during connection diagnostics: {e}")
        
        self.connection_diagnostics_done = True

    async def connect(self):
        """Connect to Binance WebSocket"""
        current_time = time.time()
        
        # Rate limit connection attempts (not more than once per 5 seconds)
        if current_time - self.last_connection_attempt < 5 and self.retry_count > 0:
            wait_time = 5 - (current_time - self.last_connection_attempt)
            logger.info(f"Rate limiting connection attempts. Waiting {wait_time:.2f}s before next attempt")
            await asyncio.sleep(wait_time)
            
        self.last_connection_attempt = time.time()
        logger.info(f"Connecting to {self.url}")
        
        # First connection attempt, run diagnostics
        if self.retry_count == 0 and not self.connection_diagnostics_done:
            await self.perform_connection_diagnostics()
        
        try:
            # Configure SSL context with modern secure defaults
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.options |= ssl.OP_NO_SSLv2
            ssl_context.options |= ssl.OP_NO_SSLv3
            ssl_context.options |= ssl.OP_NO_TLSv1
            ssl_context.options |= ssl.OP_NO_TLSv1_1
            
            # For debugging: disable certificate verification 
            # (not recommended for production)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Log network configuration
            logger.info(f"Attempting WebSocket connection with SSL context: verify_mode={ssl_context.verify_mode}, check_hostname={ssl_context.check_hostname}")
            
            # If we have aiohttp available, try to use it with custom DNS
            if AIOHTTP_AVAILABLE:
                try:
                    import importlib.metadata
                    aiohttp_version = importlib.metadata.version('aiohttp')
                    websockets_version = importlib.metadata.version('websockets')
                    logger.info(f"Using aiohttp version {aiohttp_version}, websockets version {websockets_version}")
                except:
                    pass
                    
                # Try a test HTTP request with aiohttp and custom DNS
                try:
                    resolver = aiohttp.resolver.AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"])
                    timeout = aiohttp.ClientTimeout(total=CONNECTION_TIMEOUT)
                    connector = aiohttp.TCPConnector(resolver=resolver, ssl=False)
                    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                        async with session.get('https://api.binance.com/api/v3/ping') as response:
                            if response.status == 200:
                                logger.info("Successfully connected to Binance API via HTTP (aiohttp)")
                            else:
                                logger.warning(f"HTTP connection test returned status {response.status}")
                except Exception as e:
                    logger.warning(f"aiohttp HTTP test connection failed: {e}")
            
            # Parse the URL to get host and port
            import urllib.parse
            parsed_url = urllib.parse.urlparse(self.url)
            host = parsed_url.netloc.split(':')[0]
            port = 443 if parsed_url.scheme == 'wss' else 80
            if ':' in parsed_url.netloc:
                port = int(parsed_url.netloc.split(':')[1])
                
            # Try to resolve the hostname using custom DNS first
            try:
                ip_address = None
                if DNSPYTHON_AVAILABLE:
                    try:
                        resolver = dns.resolver.Resolver()
                        resolver.nameservers = ['8.8.8.8', '8.8.4.4']
                        resolver.timeout = DNS_TIMEOUT
                        resolver.lifetime = DNS_TIMEOUT
                        
                        answers = resolver.resolve(host, 'A')
                        ip_address = answers[0].address
                        logger.info(f"Custom DNS resolved {host} to {ip_address}")
                        
                        # If we have a resolved IP, modify the URL to use it directly
                        if ip_address:
                            # Preserve the port if it exists
                            if ':' in parsed_url.netloc:
                                original_port = parsed_url.netloc.split(':')[1]
                                direct_netloc = f"{ip_address}:{original_port}"
                            else:
                                direct_netloc = ip_address
                                
                            # Create a new URL with the IP address
                            direct_url = urllib.parse.urlunparse((
                                parsed_url.scheme,
                                direct_netloc,
                                parsed_url.path,
                                parsed_url.params,
                                parsed_url.query,
                                parsed_url.fragment
                            ))
                            
                            logger.info(f"Using direct IP URL: {direct_url}")
                            self.websocket = await asyncio.wait_for(
                                websockets.connect(
                                    direct_url,
                                    ssl=ssl_context,
                                    ping_interval=20,
                                    ping_timeout=30,
                                    close_timeout=10,
                                    max_size=None,
                                    max_queue=None
                                ),
                                timeout=CONNECTION_TIMEOUT
                            )
                            logger.info(f"Successfully connected using direct IP address")
                            connected = True
                    except Exception as dns_error:
                        logger.error(f"Custom DNS resolution failed: {dns_error}")
                        connected = False
                else:
                    connected = False
                    
                # If custom DNS connection failed, try regular connection
                if not connected:
                    logger.info(f"Falling back to regular WebSocket connection")
                    self.websocket = await asyncio.wait_for(
                        websockets.connect(
                            self.url,
                            ssl=ssl_context,
                            ping_interval=20,
                            ping_timeout=30,
                            close_timeout=10,
                            max_size=None,  # No limit on message size
                            max_queue=None  # No limit on queue size
                        ),
                        timeout=CONNECTION_TIMEOUT
                    )
            except Exception as connection_error:
                # If both connection methods failed, log and re-raise
                logger.error(f"All connection methods failed: {connection_error}")
                raise
            
            # Send a test message to validate the connection
            try:
                await asyncio.wait_for(
                    self.websocket.send(json.dumps({"method": "LIST_SUBSCRIPTIONS", "id": 1})),
                    timeout=5.0
                )
                test_response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                logger.info(f"Test message response: {test_response}")
            except Exception as e:
                # Some streams don't respond to our test message - that's okay
                logger.debug(f"Test message failed, but connection may still be good: {e}")
            
            logger.info(f"Successfully connected to Binance WebSocket for {self.symbol}")
            self.connection_active = True
            self.retry_count = 0
            self.backoff_time = INITIAL_BACKOFF
            return True
        except asyncio.TimeoutError:
            logger.error(f"Connection attempt timed out after {CONNECTION_TIMEOUT} seconds")
            self.connection_active = False
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Try to get more network information
            try:
                parsed_url = self.url.split("://")[1].split("/")[0]
                host = parsed_url.split(":")[0] if ":" in parsed_url else parsed_url
                logger.info(f"Attempting to resolve hostname: {host}")
                
                # Try to resolve with custom DNS first
                if DNSPYTHON_AVAILABLE:
                    try:
                        resolver = dns.resolver.Resolver()
                        resolver.nameservers = ['8.8.8.8', '8.8.4.4']
                        answers = resolver.resolve(host, 'A')
                        ip_address = answers[0].address
                        logger.info(f"Custom DNS resolved {host} to IP: {ip_address}")
                    except Exception as custom_dns_error:
                        logger.error(f"Custom DNS resolution failed: {custom_dns_error}")
                        # Fall back to system DNS
                        ip_address = socket.gethostbyname(host)
                        logger.info(f"System DNS resolved {host} to IP: {ip_address}")
                else:
                    # Use system DNS
                    ip_address = socket.gethostbyname(host)
                    logger.info(f"Resolved {host} to IP: {ip_address}")
            except Exception as dns_error:
                logger.error(f"Could not resolve DNS: {dns_error}")
                
            self.connection_active = False
            return False

    async def disconnect(self):
        """Disconnect from the WebSocket"""
        if self.websocket:
            try:
                await self.websocket.close()
                self.websocket = None
                self.connection_active = False
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")

    async def receive_message(self):
        """Receive a single message from the WebSocket"""
        if not self.websocket or not self.connection_active:
            success = await self.connect()
            if not success:
                await self.handle_reconnection()
                return None
        
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
            return message
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for message from WebSocket")
            if self.auto_reconnect:
                await self.handle_reconnection()
            return None
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
            self.connection_active = False
            if self.auto_reconnect:
                await self.handle_reconnection()
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            self.connection_active = False
            if self.auto_reconnect:
                await self.handle_reconnection()
            return None

    async def handle_messages(self):
        """Process incoming WebSocket messages"""
        while True:
            try:
                if not self.websocket or not self.connection_active:
                    success = await self.connect()
                    if not success:
                        await self.handle_reconnection()
                        continue

                message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                if self.message_processor:
                    await self.message_processor.process_message(message)
                
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for message from WebSocket")
                if self.auto_reconnect:
                    await self.handle_reconnection()
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                self.connection_active = False
                if self.auto_reconnect:
                    await self.handle_reconnection()
                else:
                    break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                self.connection_active = False
                if self.auto_reconnect:
                    await self.handle_reconnection()
                else:
                    break

    async def handle_reconnection(self):
        """Handle reconnection with exponential backoff"""
        if self.retry_count >= self.max_retries:
            logger.error(f"Maximum retry attempts ({self.max_retries}) reached. Stopping.")
            return False

        self.retry_count += 1
        
        # Check if error might be related to rate limiting
        if self.retry_count > EXTENDED_BACKOFF_THRESHOLD:
            # Apply extended backoff for potential rate limit issues
            backoff = max(30, self.backoff_time * 2)
        else:
            # Regular exponential backoff
            backoff = self.backoff_time * 2
        
        self.backoff_time = backoff
        logger.warning(f"Attempting to reconnect in {backoff} seconds (attempt {self.retry_count}/{self.max_retries})")
        await asyncio.sleep(backoff)
        
        # Close existing websocket if it exists
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None
            self.connection_active = False
            
        return await self.connect()

    async def run(self):
        """Run the WebSocket client"""
        try:
            success = await self.connect()
            if not success:
                logger.error("Failed to establish initial connection")
                return
                
            await self.handle_messages()
        except Exception as e:
            logger.error(f"Error in WebSocket client run loop: {e}")
            logger.error(traceback.format_exc())
