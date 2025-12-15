#!/usr/bin/env python3
"""
Custom Bing Wallpaper Downloader
A modified version of bingwallpaperpy that allows specifying output directory and filename.
"""

import argparse
import sys
from pathlib import Path
from PIL import Image
from io import BytesIO
import requests
import xml.etree.ElementTree as ET

# Default settings
DEFAULT_MARKET = "de-DE"
DEFAULT_OFFSET = "0"
DEFAULT_COUNT = "1"
DEFAULT_FILENAME = "bingwallpaper.png"
BASE_URL = "https://www.bing.com"

def download_bing_wallpaper(output_path=None, market=DEFAULT_MARKET, offset=DEFAULT_OFFSET, count=DEFAULT_COUNT):
    """
    Download today's Bing wallpaper.
    
    Args:
        output_path: Path where to save the image (can be file or directory)
        market: Market/locale for Bing (e.g., 'de-DE', 'en-US')
        offset: Days offset from today (0 = today, 1 = yesterday, etc.)
        count: Number of images to get (usually 1)
    
    Returns:
        Path to the downloaded image
    """
    # Construct the API URL
    url = f"{BASE_URL}/HPImageArchive.aspx?format=xml&idx={offset}&n={count}&mkt={market}"
    
    # Get the image list
    resp = requests.get(url)
    if not resp.ok:
        raise Exception(f"Failed to fetch image list: {resp.status_code}")
    
    # Parse XML response
    xml = ET.fromstring(resp.content)
    img_url = xml.find("./image/url")
    if img_url is None or img_url.text is None:
        raise Exception("No image URL found in response")
    
    # Download the image
    full_img_url = BASE_URL + img_url.text
    print(f"Downloading: {full_img_url}")
    
    img_resp = requests.get(full_img_url)
    if not img_resp.ok:
        raise Exception(f"Failed to download image: {img_resp.status_code}")
    
    # Determine output path
    if output_path is None:
        # Default behavior: save to Downloads or /tmp
        dest_dir = Path.home() / "Downloads" if (Path.home() / "Downloads").exists() else Path("/tmp")
        dest_path = dest_dir / DEFAULT_FILENAME
    else:
        output_path = Path(output_path)
        if output_path.is_dir():
            # If it's a directory, append default filename
            dest_path = output_path / DEFAULT_FILENAME
        else:
            # If it's a file path, use it directly
            dest_path = output_path
    
    # Ensure the output directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the image
    img = Image.open(BytesIO(img_resp.content))
    img.save(dest_path)
    
    print(f"Saved to: {dest_path}")
    return dest_path

def main():
    parser = argparse.ArgumentParser(
        description="Download Bing daily wallpaper with customizable output location",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Save to default location
  %(prog)s ~/Pictures/wallpapers/            # Save to directory with default filename
  %(prog)s ~/Pictures/wallpapers/my_wall.jpg # Save to specific file
  %(prog)s -m en-US                          # Use US market
  %(prog)s -o 1                              # Get yesterday's wallpaper
        """
    )
    
    parser.add_argument(
        "output", 
        nargs="?", 
        help="Output path (file or directory). If directory, uses default filename."
    )
    
    parser.add_argument(
        "-m", "--market",
        default=DEFAULT_MARKET,
        help=f"Market/locale (default: {DEFAULT_MARKET})"
    )
    
    parser.add_argument(
        "-o", "--offset",
        default=DEFAULT_OFFSET,
        type=int,
        help=f"Days offset from today (default: {DEFAULT_OFFSET})"
    )
    
    parser.add_argument(
        "-c", "--count",
        default=DEFAULT_COUNT,
        type=int,
        help=f"Number of images to download (default: {DEFAULT_COUNT})"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        dest_path = download_bing_wallpaper(
            output_path=args.output,
            market=args.market,
            offset=str(args.offset),
            count=str(args.count)
        )
        
        if args.verbose:
            print(f"Successfully downloaded wallpaper to: {dest_path}")
        
        # Exit with success
        sys.exit(0)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
