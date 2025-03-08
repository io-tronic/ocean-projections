import cv2
import os
import csv
import argparse
import sys
import time

# Cross-platform single-character keyboard input
try:
    import msvcrt
    def get_key():
        """Get a single character from stdin on Windows."""
        return msvcrt.getch().decode("utf-8", errors="ignore")
except ImportError:
    import termios
    import tty

    def get_key():
        """Get a single character from stdin on Unix."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def main():
    parser = argparse.ArgumentParser(
    description="Script to scan items with a webcam, crop, measure color (HSL), and record to CSV."
    )
    parser.add_argument("--xcrop", type=float, default=1.0, 
                        help="Fraction of width to keep in the center. Default=1.0 (no crop).")
    parser.add_argument("--ycrop", type=float, default=1.0, 
                        help="Fraction of height to keep in the center. Default=1.0 (no crop).")
    parser.add_argument("--camera-index", type=int, default=0,
                        help="Index of the webcam to use. Default=0")

    args = parser.parse_args()
    xcrop = args.xcrop
    ycrop = args.ycrop
    camera_index = args.camera_index

    # Create output directories if they do not exist
    os.makedirs("scanimg", exist_ok=True)
    os.makedirs("cropimg", exist_ok=True)

    # Prompt user for the starting index
    start_index_str = input("Enter the current index: ")
    try:
        index = int(start_index_str)
    except ValueError:
        print("Invalid index. Please enter a number.")
        sys.exit(1)

    csv_filename = "scandata.csv"
    file_exists = os.path.isfile(csv_filename)

    print("Press SPACE to capture the image, or ESC to quit.")

    while True:
        # 1) Print current index
        print(f"Current index: {index}")

        # 2) Wait for key press
        key = get_key()
        
        # If ESC (ASCII 27) is pressed, exit program
        if ord(key) == 27:
            print("ESC pressed. Exiting...")
            break

        # If SPACE (ASCII 32) is pressed, capture
        if ord(key) == 32:
            # 3) Capture from webcam
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                print("Error: Could not open webcam.")
                break

            # Warm up the camera by discarding a few frames.
            for _ in range(10):
                cap.read()

            # A short wait to let auto-exposure settle.
            time.sleep(0.1)

            # 3. Now capture the actual frame.
            ret, frame = cap.read()

            cap.release()

            if not ret:
                print("Failed to capture image from webcam.")
                break

            # Continue saving, cropping, etc.
            scan_path = f"./scanimg/{index:04d}.jpg"
            cv2.imwrite(scan_path, frame)
            print(f"Saved image to {scan_path}")

            # 4) Save raw scan image
            scan_path = f"./scanimg/{index:04d}.jpg"
            cv2.imwrite(scan_path, frame)
            print(f"Saved image to {scan_path}")

            # 5) Crop the image (centered) according to xcrop, ycrop
            height, width = frame.shape[:2]

            crop_w = int(width * xcrop)
            crop_h = int(height * ycrop)

            # Calculate top-left corner for centered crop
            x_start = (width - crop_w) // 2
            y_start = (height - crop_h) // 2
            x_end = x_start + crop_w
            y_end = y_start + crop_h

            cropped = frame[y_start:y_end, x_start:x_end]

            # 6) Save cropped image
            crop_path = f"./cropimg/{index:04d}.jpg"
            cv2.imwrite(crop_path, cropped)
            print(f"Saved cropped image to {crop_path}")

            # 7) Compute average HSL
            hls_img = cv2.cvtColor(cropped, cv2.COLOR_BGR2HLS)  # HLS order in OpenCV
            # Split channels
            h_channel, l_channel, s_channel = cv2.split(hls_img)
            
            # Calculate mean of each channel
            hue_avg = h_channel.mean()
            light_avg = l_channel.mean()
            sat_avg = s_channel.mean()

            # 8) Append to CSV file
            # If the file does not exist, create it with headers
            with open(csv_filename, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["index", "scan path", "cropped path", "hue", "saturation", "lightness"])
                    file_exists = True  # So we don't rewrite header again
                writer.writerow([index, scan_path, crop_path, hue_avg, sat_avg, light_avg])
            print(f"Appended data to {csv_filename}")

            # 9) Increment the index
            index += 1
        else:
            # If some other key is pressed, ignore/continue
            continue

if __name__ == "__main__":
    main()
