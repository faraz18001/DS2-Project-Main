import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def scrape_pdfs(url, download_folder):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        print(f"Created directory: {download_folder}")

    # Set headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': url
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to access {url}. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links to PDFs
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link['href']
        if 'download_file.php' in href:
            pdf_url = urljoin(url, href)
            # Try to get the filename from the query parameter
            import urllib.parse
            parsed = urllib.parse.urlparse(pdf_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'files' in query_params:
                file_url = query_params['files'][0]
                pdf_name = os.path.join(download_folder, file_url.split('/')[-1])
                
                print(f"Downloading {file_url} to {pdf_name}...")
                
                try:
                    pdf_response = requests.get(file_url, headers=headers)
                    if pdf_response.status_code == 200:
                        with open(pdf_name, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"Successfully downloaded {pdf_name}")
                    else:
                        print(f"Failed to download {file_url}. Status code: {pdf_response.status_code}")
                except Exception as e:
                    print(f"Error downloading {file_url}: {e}")

if __name__ == "__main__":
    target_url = "https://pastpapers.papacambridge.com/papers/caie/o-level-physics-5054-2025-oct-nov"
    data_folder = "data"
    scrape_pdfs(target_url, data_folder)
