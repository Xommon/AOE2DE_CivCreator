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
        'https://ageofempires.fandom.com/wiki/Britons', 'https://ageofempires.fandom.com/wiki/Franks', 'https://ageofempires.fandom.com/wiki/Goths', 'https://ageofempires.fandom.com/wiki/Teutons', 'https://ageofempires.fandom.com/wiki/Japanese_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Chinese_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Byzantines_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Persians_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Saracens', 'https://ageofempires.fandom.com/wiki/Turks', 'https://ageofempires.fandom.com/wiki/Vikings_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Mongols_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Celts', 'https://ageofempires.fandom.com/wiki/Spanish_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Aztecs_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Mayans', 'https://ageofempires.fandom.com/wiki/Huns', 'https://ageofempires.fandom.com/wiki/Koreans', 'https://ageofempires.fandom.com/wiki/Italians_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Hindustanis', 'https://ageofempires.fandom.com/wiki/Incas', 'https://ageofempires.fandom.com/wiki/Magyars', 'https://ageofempires.fandom.com/wiki/Slavs', 'https://ageofempires.fandom.com/wiki/Portuguese_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Ethiopians_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Malians_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Berbers_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Khmer', 'https://ageofempires.fandom.com/wiki/Malay', 'https://ageofempires.fandom.com/wiki/Burmese', 'https://ageofempires.fandom.com/wiki/Vietnamese', 'https://ageofempires.fandom.com/wiki/Bulgarians', 'https://ageofempires.fandom.com/wiki/Tatars_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Cumans', 'https://ageofempires.fandom.com/wiki/Lithuanians', 'https://ageofempires.fandom.com/wiki/Burgundians', 'https://ageofempires.fandom.com/wiki/Sicilians', 'https://ageofempires.fandom.com/wiki/Poles', 'https://ageofempires.fandom.com/wiki/Bohemians', 'https://ageofempires.fandom.com/wiki/Dravidians', 'https://ageofempires.fandom.com/wiki/Bengalis', 'https://ageofempires.fandom.com/wiki/Gurjaras', 'https://ageofempires.fandom.com/wiki/Romans_(Age_of_Empires_II)', 'https://ageofempires.fandom.com/wiki/Armenians', 'https://ageofempires.fandom.com/wiki/Georgians'
    ],
    r'C:\Users\Micheal Q\OneDrive\Documents\GitHub\AOE2DE_CivCreator\Sounds'
)