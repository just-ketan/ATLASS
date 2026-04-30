import arxiv
import os
import time
import requests

class ArxivDownloader:
    def __init__(self, download_dir="data/raw_papers", max_retries = 3):
        self.download_dir = download_dir
        self.max_retries = max_retries
        os.makedirs(download_dir, exist_ok=True)

    def download(self, arxiv_id):
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())

        pdf_url = paper.pdf_url
        pdf_path = os.path.join(self.download_dir , f"{arxiv_id}.pdf")

        for attempt in range(self.max_retries):
            try:
                print(f"Attempt: {attempt+1}....")
                response = requests.get(pdf_url, stream=True, timeout=10)
                response.raise_for_status()

                with open(pdf_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                                f.write(chunk)
                print("Download complete:", pdf_path)
                return pdf_path
            except Exception as e:
                print("DownloadFailed:", e)
                if attempt < self.max_retries-1:
                    print("Retrying....\n")
                    time.sleep(2)
                else:
                    raise RuntimeError("Failed to download paper after retries !!")