import os
import requests
import zipfile
import io
import time
from datetime import datetime

class CVMClient:
    """
    Client to download public financial data from CVM (Dados Abertos).
    """
    BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/"

    def __init__(self, data_dir="data/cvm"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def download_file(self, url, filename):
        """
        Downloads a file from URL to self.data_dir/filename with resume support and progress bar.
        """
        final_path = os.path.join(self.data_dir, filename)
        temp_path = final_path + ".tmp"
        
        # Resume support: Check if final file already exists and has size > 0
        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
            print(f"File {filename} already exists. Skipping download.")
            return final_path

        print(f"Downloading {filename}...")
        
        # Resume support for partial downloads? No, complex for HTTP unless Range header supported.
        # Let's just download fresh to .tmp and rename on success.
        
        for attempt in range(3):
            try:
                # User-Agent is sometimes required by gov sites
                headers = {'User-Agent': 'Mozilla/5.0 (compatible; AnalyticsBot/1.0)'}
                response = requests.get(url, headers=headers, stream=True, timeout=300) 
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                
                # Use tqdm for progress bar
                from tqdm import tqdm
                with open(temp_path, 'wb') as f, tqdm(
                    desc=filename,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        size = f.write(chunk)
                        bar.update(size)
                
                # Verify size if content-length was given?
                if total_size > 0 and os.path.getsize(temp_path) < total_size:
                     raise Exception("Incomplete download")

                # Atomic rename
                os.rename(temp_path, final_path)
                print(f"Successfully downloaded {filename}")
                return final_path

            except Exception as e:
                print(f"Attempt {attempt+1} failed to download {url}: {e}")
                time.sleep(5) # Wait before retry
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None

    def fetch_annual_reports(self, year):
        """
        Downloads DFP (Demonstrações Financeiras Padronizadas) for a given year.
        """
        # URL Pattern: http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_YYYY.zip
        filename = f"dfp_cia_aberta_{year}.zip"
        url = f"{self.BASE_URL}DFP/DADOS/{filename}"
        
        zip_path = self.download_file(url, filename)
        if zip_path:
            return self._extract_zip(zip_path)
        return []

    def fetch_quarterly_reports(self, year):
        """
        Downloads ITR (Informações Trimestrais) for a given year.
        """
        # URL Pattern: http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_YYYY.zip
        filename = f"itr_cia_aberta_{year}.zip"
        url = f"{self.BASE_URL}ITR/DADOS/{filename}"
        
        zip_path = self.download_file(url, filename)
        if zip_path:
            return self._extract_zip(zip_path)
        return []

    def _extract_zip(self, zip_path):
        """
        Extracts ZIP content to a folder named after the file.
        Returns list of extracted file paths.
        """
        extracted_files = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract to a subdir to avoid clutter
                extract_dir = os.path.splitext(zip_path)[0]
                os.makedirs(extract_dir, exist_ok=True)
                zip_ref.extractall(extract_dir)
                
                for name in zip_ref.namelist():
                    extracted_files.append(os.path.join(extract_dir, name))
            
            print(f"Extracted {len(extracted_files)} files to {extract_dir}")
            return extracted_files
        except Exception as e:
            print(f"Failed to extract {zip_path}: {e}")
            return []

if __name__ == "__main__":
    # Test run
    client = CVMClient()
    current_year = datetime.now().year
    
    # Try downloading last year's annual report
    files = client.fetch_annual_reports(current_year - 1)
    print("Downloaded files:", files)
