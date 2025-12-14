
import os
import requests
import zipfile
import shutil
import io

GITHUB_REPO = "oschwartz10612/poppler-windows"
ASSETS_DIR = "installer_assets"

def download_poppler():
    print(f"Finding latest Poppler release from {GITHUB_REPO}...")
    
    # Get latest release data
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        
        # Find zip asset
        zip_url = None
        for asset in data.get('assets', []):
            if asset['name'].endswith('.zip'):
                zip_url = asset['browser_download_url']
                print(f"Found asset: {asset['name']}")
                break
        
        if not zip_url:
            print("No .zip asset found in latest release.")
            return

        print(f"Downloading from: {zip_url}")
        print("This might take a minute...")
        
        # Download
        r = requests.get(zip_url, stream=True)
        r.raise_for_status()
        
        # Unzip
        print("Extracting...")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            # Extract to temp
            z.extractall(ASSETS_DIR)
            
        # Find the extracted folder (it usually has a name like Release-24.08...)
        extracted_dirs = [d for d in os.listdir(ASSETS_DIR) if d.startswith("Release") or d.startswith("poppler")]
        
        # Identify the right one and rename to 'poppler'
        final_poppler_path = os.path.join(ASSETS_DIR, "poppler")
        
        # Clean up old if exists
        if os.path.exists(final_poppler_path):
            shutil.rmtree(final_poppler_path)
            
        for d in extracted_dirs:
            full_d = os.path.join(ASSETS_DIR, d)
            if os.path.isdir(full_d):
                # Check if it has 'bin'
                if os.path.exists(os.path.join(full_d, "bin")) or os.path.exists(os.path.join(full_d, "Library", "bin")):
                    print(f"Renaming {d} to poppler...")
                    shutil.move(full_d, final_poppler_path)
                    break
        
        print("Poppler downloaded and set up successfully!")
        print(f"Location: {os.path.abspath(final_poppler_path)}")

    except Exception as e:
        print(f"Error downloading Poppler: {e}")

if __name__ == "__main__":
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
    download_poppler()
