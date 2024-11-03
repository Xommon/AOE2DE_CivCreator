# Extract sound files from a website
import os
import requests
from bs4 import BeautifulSoup

def download_audio_files(urls, download_folder):
    try:
        # Ensure the download folder exists
        os.makedirs(download_folder, exist_ok=True)

        # Process each URL
        for url in urls:
            print(f"\nProcessing: {url}")
            try:
                # Send a request to the website
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors

                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all <audio> tags and get the 'src' attribute if it exists
                audio_links = set()
                for audio_tag in soup.find_all('audio', src=True):
                    audio_src = audio_tag['src']
                    # If the URL is relative, make it absolute
                    full_url = requests.compat.urljoin(url, audio_src)
                    audio_links.add(full_url)

                # Download each audio file
                if audio_links:
                    print("Found audio files. Downloading...")
                    for link in audio_links:
                        # Extract the file name from the link
                        parts = link.split('/')
                        if len(parts) > 7:
                            file_name = parts[7].split('?')[0]  # Get text after the 7th slash, ignoring query parameters
                        else:
                            file_name = os.path.basename(link.split('?')[0])  # Fallback to the original file name

                        # Remove "_AoE2.ogg" from the file name if it exists
                        if file_name.endswith('_AoE2.ogg'):
                            file_name = file_name.replace('_AoE2.ogg', '')

                        # Skip downloading if "jingle" or "theme" is in the file name
                        if "jingle" in file_name.lower() or "theme" in file_name.lower():
                            print(f"Skipping: {file_name} (contains 'jingle' or 'theme')")
                            continue

                        file_name += '.ogg'  # Ensure the file has a .ogg extension
                        file_path = os.path.join(download_folder, file_name)

                        # Download the audio file
                        try:
                            file_response = requests.get(link)
                            file_response.raise_for_status()  # Raise an exception for HTTP errors

                            # Save the file to the specified folder
                            with open(file_path, 'wb') as file:
                                file.write(file_response.content)

                            print(f"Downloaded: {file_name}")
                        except requests.RequestException as e:
                            print(f"Failed to download {link}: {e}")
                else:
                    print("No audio files found on the provided webpage.")

            except requests.RequestException as e:
                print(f"Error fetching the webpage: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
download_audio_files(
    [
        'https://static.wikia.nocookie.net/ageofempires/images/3/32/Byzantine_villagermale_resourcegather_inorm_clowest_01_mp3.mp3/revision/latest?cb=20231216072422'
    ],
    r'C:\Users\Micheal Q\OneDrive\Documents\GitHub\AOE2DE_CivCreator\Sounds\Downloads'
)