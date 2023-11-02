import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python test.py [video_path]")
        return

    video_path = sys.argv[1]

    embedded_video_path = "https://voda-iresource2.s3.ap-northeast-2.amazonaws.com/test/small.mp4"
    print(f"Embedded Video Local Path: {embedded_video_path}")

if __name__ == "__main__":
    main()
