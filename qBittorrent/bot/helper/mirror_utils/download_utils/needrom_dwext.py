import re
import time
import httpx
import random
import asyncio
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from bot.helper.ext_utils.exceptions import NeedromException
from bot import LOGGER

class NeedromBypass:
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.needrom.com/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
        )
        # Enhanced patterns to better match download links
        self.download_pattern = re.compile(r'href=[\'"]([^\'"]*\.(?:zip|rar|7z)[^\'"]*)[\'"]')
        self.server_pattern = re.compile(r'href=[\'"]([^\'"]*/(?:server|download)/download\.php[^\'"]*)[\'"]')
        self.js_download_pattern = re.compile(r'downloadUrl\s*=\s*[\'"]([^\'"]+)[\'"]')
        
        # Patterns for detecting countdown and auto messages
        self.auto_message_pattern = re.compile(
            r'(your download is ready|please wait|checking your browser|redirecting in \d+ seconds|searching for mirrors|countDown)',
            re.IGNORECASE
        )
        
        # Block list for ad scripts (similar to the UserScript)
        self.blocked_scripts = [
            r'colorbox\/home\/jquery\.colorbox.*\.min\.js',
            r'colorbox\/server\/jquery\.colorbox.*\.min\.js',
            r'adblock',
            r'popunder'
        ]
        
        # Track download attempts
        self.retry_count = 0
        self.max_retries = 3
        
    async def close(self):
        await self.client.aclose()
        
    async def generate_cookies(self):
        """Generate required cookies to bypass Needrom protection"""
        timestamp = int(time.time())
        expiry = timestamp + 86400 + random.randint(100, 1000)
        
        # Set required cookies
        self.client.cookies.set(
            "Needromfile", 
            "0",
            domain=".needrom.com", 
            path="/", 
            expires=expiry
        )
        
        # Add additional cookies to bypass protection
        self.client.cookies.set(
            "has_js", 
            "1",
            domain=".needrom.com", 
            path="/", 
            expires=expiry
        )
        
        # Add a fake download history cookie
        self.client.cookies.set(
            "NeedromDLHistory", 
            f"{random.randint(1000000, 9999999)}",
            domain=".needrom.com", 
            path="/", 
            expires=expiry
        )
        
        LOGGER.debug("Generated necessary cookies for Needrom")
    
    async def extract_download_link(self, url):
        """Extract direct download link from Needrom page"""
        LOGGER.info(f"Extracting download link from: {url}")
        
        await self.generate_cookies()
        self.retry_count = 0
        
        try:
            # First request to the download page
            response = await self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NeedromException(f"Failed to access Needrom page: {str(e)}")
        
        # Extract the server download link
        server_url = self._extract_server_link(response.text, url)
        
        if not server_url:
            raise NeedromException("No server download link found on the page")
        
        LOGGER.debug(f"Found server URL: {server_url}")
        
        # Simulate human-like behavior with a small delay
        await asyncio.sleep(random.uniform(1.5, 3.0))
        
        # Access the server download page
        try:
            response = await self.client.get(server_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NeedromException(f"Failed to access server download page: {str(e)}")
        
        # Extract file information
        file_info = self._extract_file_info(response.text)
        
        if not file_info:
            raise NeedromException("Could not extract file information")
        
        LOGGER.debug(f"File info: {file_info}")
        
        # First try to get direct link
        direct_link = self._extract_direct_link(response.text)
        
        # If not found, try to handle delayed downloads
        if not direct_link:
            direct_link = await self._handle_delayed_download(response.text, server_url)
        
        # If still not found, try to extract from JS
        if not direct_link:
            direct_link = self._extract_from_javascript(response.text)
        
        if not direct_link:
            # One last attempt with a different approach
            direct_link = await self._try_alternative_extraction(server_url)
            
        if not direct_link:
            raise NeedromException("Could not find direct download link after multiple attempts")
        
        LOGGER.info(f"Successfully extracted direct download link")
        
        return {
            "direct_link": direct_link,
            "file_info": file_info
        }
    
    def _extract_server_link(self, html_content, base_url=None):
        """Extract server download link from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for download buttons
        for button in soup.select('.btn-danger, .btn-primary, .btn-success, a[title*="Server"], a[title*="Download"]'):
            href = button.get('href')
            if href and ('server/download.php' in href or 'download/download.php' in href):
                return urljoin(base_url, href) if base_url else href
        
        # If buttons not found, try regex pattern
        match = self.server_pattern.search(html_content)
        if match:
            return urljoin(base_url, match.group(1)) if base_url else match.group(1)
        
        # Try a broader search
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            if 'download.php' in href:
                return urljoin(base_url, href) if base_url else href
        
        return None
    
    def _extract_file_info(self, html_content):
        """Extract file information (name, size, extension) from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        file_info = {}
        
        # Try to find file information in different ways
        # Method 1: Look for spans with specific text
        file_name_element = soup.select_one('span:-soup-contains("File Name")')
        if file_name_element and file_name_element.find_next('span'):
            file_info['filename'] = file_name_element.find_next('span').get_text(strip=True)
        
        file_size_element = soup.select_one('span:-soup-contains("File Size")')
        if file_size_element and file_size_element.find_next('span'):
            file_info['filesize'] = file_size_element.find_next('span').get_text(strip=True)
            
        file_ext_element = soup.select_one('span:-soup-contains("File Extension")')
        if file_ext_element and file_ext_element.find_next('span'):
            file_info['extension'] = file_ext_element.find_next('span').get_text(strip=True)
        
        # Method 2: Try to find file info in tables
        if not file_info.get('filename'):
            for row in soup.select('tr'):
                cells = row.select('td')
                if len(cells) >= 2:
                    header = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if 'file name' in header:
                        file_info['filename'] = value
                    elif 'file size' in header:
                        file_info['filesize'] = value
                    elif 'extension' in header:
                        file_info['extension'] = value
        
        # Method 3: Look for headers and metadata
        if not file_info.get('filename'):
            h1 = soup.select_one('h1, h2, .file-name, .filename')
            if h1:
                file_info['filename'] = h1.get_text(strip=True)
        
        return file_info if file_info else None
    
    def _extract_direct_link(self, html_content):
        """Extract direct download link from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for download buttons with links to archives
        for a_tag in soup.select('a.btn-danger, a.btn-primary, a.btn-success, a[href*=".zip"], a[href*=".rar"], a[href*=".7z"]'):
            href = a_tag.get('href')
            if href and not href.startswith('javascript'):
                if href.endswith('.zip') or href.endswith('.rar') or href.endswith('.7z') or '?' in href:
                    return href
        
        # Try regex pattern
        match = self.download_pattern.search(html_content)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_from_javascript(self, html_content):
        """Extract download link from JavaScript code"""
        # Look for downloadUrl variable in JavaScript
        match = self.js_download_pattern.search(html_content)
        if match:
            return match.group(1)
        
        # Look for embedded JSON with file URLs
        json_match = re.search(r'fileData\s*=\s*({.*?})', html_content, re.DOTALL)
        if json_match:
            try:
                import json
                data = json.loads(json_match.group(1))
                if 'url' in data:
                    return data['url']
            except:
                pass
        
        return None
    
    async def _handle_delayed_download(self, html_content, server_url):
        """Handle download pages with countdowns or delays"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for countdown elements or waiting messages
        countdown_element = soup.select_one('#countdowntimertxt, .countdowntimertxt, #countdown, .countdown')
        
        if countdown_element or self.auto_message_pattern.search(html_content):
            LOGGER.debug("Detected countdown or waiting message, attempting to bypass...")
            
            # Try to find the countdown time
            wait_time_match = re.search(r'var\s+countDown\s*=\s*(\d+)', html_content)
            wait_time = int(wait_time_match.group(1)) if wait_time_match else 5
            
            # Add a small buffer to ensure the countdown completes
            wait_time += 2
            
            LOGGER.debug(f"Waiting for {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            
            # After waiting, try to access the download link again
            try:
                # Add a specific referer header to improve bypass success
                headers = self.client.headers.copy()
                headers['Referer'] = server_url
                
                # Try POST request instead of GET in some cases
                if "id=" in server_url:
                    form_data = {'download': '1', 'agree': '1'}
                    response = await self.client.post(server_url, data=form_data, headers=headers)
                else:
                    response = await self.client.get(server_url, headers=headers)
                
                response.raise_for_status()
                
                # Try to extract direct link from the response
                direct_link = self._extract_direct_link(response.text)
                if direct_link:
                    return direct_link
                
                # Try to extract from JavaScript
                direct_link = self._extract_from_javascript(response.text)
                if direct_link:
                    return direct_link
                
            except httpx.HTTPError as e:
                LOGGER.error(f"Error during delayed download: {str(e)}")
                return None
        
        return None
    
    async def _try_alternative_extraction(self, server_url):
        """Attempt alternative methods to extract download link"""
        if self.retry_count >= self.max_retries:
            return None
        
        self.retry_count += 1
        LOGGER.debug(f"Trying alternative extraction method (attempt {self.retry_count})")
        
        # Method 1: Try with different headers
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": server_url,
            }
            
            response = await self.client.get(server_url, headers=headers)
            direct_link = self._extract_direct_link(response.text)
            if direct_link:
                return direct_link
            
            # Try to extract from JavaScript
            direct_link = self._extract_from_javascript(response.text)
            if direct_link:
                return direct_link
        except:
            pass
        
        # Method 2: Try to simulate form submission
        try:
            # Extract form data
            response = await self.client.get(server_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            form = soup.select_one('form')
            if form:
                form_data = {}
                for input_tag in form.select('input'):
                    name = input_tag.get('name')
                    value = input_tag.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Add required fields if missing
                if 'download' not in form_data:
                    form_data['download'] = '1'
                if 'agree' not in form_data:
                    form_data['agree'] = '1'
                
                # Submit the form
                form_action = form.get('action', server_url)
                form_url = urljoin(server_url, form_action)
                
                response = await self.client.post(form_url, data=form_data)
                
                direct_link = self._extract_direct_link(response.text)
                if direct_link:
                    return direct_link
                
                # Try to extract from JavaScript
                direct_link = self._extract_from_javascript(response.text)
                if direct_link:
                    return direct_link
        except:
            pass
        
        return None
        
    async def download_file(self, direct_link, file_path, progress_callback=None):
        """Download file from direct link with progress tracking"""
        try:
            headers = {}
            downloaded_size = 0
            
            import os
            if os.path.exists(file_path):
                downloaded_size = os.path.getsize(file_path)
                headers['Range'] = f'bytes={downloaded_size}-'
                LOGGER.info(f"Resuming download from {downloaded_size} bytes")
            
            # Add referer to avoid download blocks
            headers['Referer'] = 'https://www.needrom.com/'
            
            with open(file_path, 'ab' if downloaded_size else 'wb') as f:
                async with self.client.stream('GET', direct_link, headers=headers) as response:
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0)) + downloaded_size
                    
                    if downloaded_size and response.status_code != 206:
                        f.close()
                        downloaded_size = 0
                        with open(file_path, 'wb') as f:
                            pass  
                    
                    downloaded = downloaded_size
                    chunk_size = 1024 * 1024  # 1MB chunks
                    
                    async for chunk in response.aiter_bytes(chunk_size):
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress = downloaded / total_size if total_size else 0
                            progress_callback(downloaded, total_size, progress)
            
            LOGGER.info(f"Download completed: {file_path}")
            return True
            
        except (httpx.HTTPError, IOError) as e:
            LOGGER.error(f"Download failed: {str(e)}")
            
            # Try to resume download after a brief delay
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                LOGGER.info("Attempting to resume download after brief delay...")
                await asyncio.sleep(3)
                return await self.download_file(direct_link, file_path, progress_callback)
                
            return False