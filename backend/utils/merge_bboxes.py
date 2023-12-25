import matplotlib.pyplot as plt
import matplotlib.patches as patches
import csv

def plot_detections(anomaly_detections, yolo_detections, output_detections, image_size=(4000, 3000)):
    """
    Plots detections from anomaly detection, YOLO, and final detections on a black background image.
    Anomaly detections, YOLO detections, and final detections are plotted in red, blue, and green, respectively.
    Detections format: [frame, x, y, x+w, y+h, ...]
    """
    # Convert lists into dictionaries grouped by frame
    grouped_anomaly_outputs = {}
    for det in anomaly_detections:
        frame = int(det[0])
        grouped_anomaly_outputs.setdefault(frame, []).append(det)

    grouped_detection_outputs = {}
    for det in yolo_detections:
        frame = int(det[0])
        grouped_detection_outputs.setdefault(frame, []).append(det)

    grouped_output_detections = {}
    for det in output_detections:
        frame = int(det[0])
        grouped_output_detections.setdefault(frame, []).append(det)

    # Set of all frames
    all_frames = set(grouped_anomaly_outputs.keys()) | set(grouped_detection_outputs.keys()) | set(grouped_output_detections.keys())

    for frame in all_frames:
        fig, ax = plt.subplots(1, figsize=(12, 9))
        ax.set_xlim(0, image_size[0])
        ax.set_ylim(image_size[1], 0)
        ax.imshow([[0,0],[0,0]], cmap='gray', extent=[0, image_size[0], 0, image_size[1]])
        ax.set_title(f"Frame {frame}")

        # Plot anomaly detections in red
        for det in grouped_anomaly_outputs.get(frame, []):
            box = det[2:6]
            rect = patches.Rectangle((box[0], box[1]), box[2], box[3], linewidth=1, edgecolor='red', facecolor='none')
            ax.add_patch(rect)

        # Plot YOLO detections in blue
        for det in grouped_detection_outputs.get(frame, []):
            box = det[2:6]
            rect = patches.Rectangle((box[0], box[1]), box[2], box[3], linewidth=1, edgecolor='blue', facecolor='none')
            ax.add_patch(rect)

        # Plot final detections in green
        for det in grouped_output_detections.get(frame, []):
            box = det[1:5]
            rect = patches.Rectangle((box[0], box[1]), box[2]-box[0], box[3]-box[1], linewidth=1, edgecolor='green', facecolor='none')
            ax.add_patch(rect)

        plt.show()


def calculate_distance(box1, box2):
    """
    Calculate the Euclidean distance between the centers of two boxes.
    """
    center1_x, center1_y = (box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2
    center2_x, center2_y = (box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2
    distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5
    return distance

# Modified function to save output to a file
def match_and_ensemble(anomaly_outputs, detection_outputs, use_anomaly, output_file):
    output = []
    confidence_threshold = 0.7
    grouped_anomaly_outputs = {}
    grouped_detection_outputs = {}

    # Group by frame number
    for det in anomaly_outputs:
        frame = int(det[0])
        grouped_anomaly_outputs.setdefault(frame, []).append(det)

    for det in detection_outputs:
        frame = int(det[0])
        grouped_detection_outputs.setdefault(frame, []).append(det)
    
    # Process each frame
    for frame in grouped_detection_outputs:
        yolo_dets = grouped_detection_outputs[frame]
        anomaly_dets = grouped_anomaly_outputs.get(frame, [])

        processed_yolo_indices = set()
        
        # Process YOLO detections first
        for idx, yl_output in enumerate(yolo_dets):
            output.append([yl_output[0], yl_output[2], yl_output[3], yl_output[2]+yl_output[4], yl_output[3]+yl_output[5], yl_output[6], yl_output[1]])
            processed_yolo_indices.add(idx)

        # Process anomaly detections if YOLO detections are not sufficient
        if use_anomaly and not processed_yolo_indices:
            for a_output in anomaly_dets:
                if a_output[6] >= confidence_threshold:            
                    output.append([a_output[0], a_output[2], a_output[3], a_output[2]+a_output[4], a_output[3]+a_output[5], a_output[6], a_output[1]])

    # Save the output to the specified file
    with open(output_file, 'w') as file:
        for detection in output:
            file.write(','.join(map(str, detection)) + '\n')
    file.close()

def read_file(file_path):
    """
    Reads a detection file and returns a list of detections.
    Each line in the file should contain comma-separated values.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    detections = [[float(x) for x in line.strip().split(',')] for line in lines]
    return detections


def read_csv_file(file_path):
    detections = []
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            detections.append([float(x) for x in row])
    return detections


# Test the final function with new criteria
if __name__ == "__main__":
    use_anomaly = True
    # Define file paths
    anomaly_file_path = '/Users/seowoo/Desktop/Development/DVA_LAB/in/anomaly.csv'
    detection_file_path = '/Users/seowoo/Desktop/Development/DVA_LAB/in/detection.csv'
    output_file_path = '/Users/seowoo/Desktop/Development/DVA_LAB/out/output.txt'

    # Read inputs from files
    anomaly_detection_output = read_file(anomaly_file_path)
    detection_output = read_file(detection_file_path)

    
    # Call the modified function with the new output file path
    output = match_and_ensemble(anomaly_detection_output, detection_output, use_anomaly=True, output_file=output_file_path)
    plot_detections(anomaly_detection_output, detection_output, output)
