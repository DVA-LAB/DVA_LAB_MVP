import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_detections(anomaly_detections, yolo_detections, final_detections, image_size=(4000, 3000)):
    """
    Plots detections from anomaly detection and YOLO on a black background image.
    Anomaly detections are plotted in red, YOLO detections in blue, and final detections in orange.
    [x, y, x+w, y+h]
    """
    fig, ax = plt.subplots(1, figsize=(12, 9))
    ax.set_xlim(0, image_size[0])
    ax.set_ylim(image_size[1], 0)
    ax.imshow([[0,0],[0,0]], cmap='gray', extent=[0, image_size[0], 0, image_size[1]])

    # Plot anomaly detections in red
    for det in anomaly_detections:
        box = det[2:6]
        rect = patches.Rectangle((box[0], box[1]), box[2], box[3], linewidth=1, edgecolor='red', facecolor='red', alpha=0.5)
        ax.add_patch(rect)

    # Plot YOLO detections in blue
    for det in yolo_detections:
        box = det[2:6]
        rect = patches.Rectangle((box[0], box[1]), box[2], box[3], linewidth=1, edgecolor='blue', facecolor='blue', alpha=0.5)
        ax.add_patch(rect)

    # Highlight final detections in orange
    for det in final_detections:
        box = det[0:4]
        rect = patches.Rectangle((box[0], box[1]), box[2]-box[0], box[3]-box[1], linewidth=1, edgecolor='orange', facecolor='none')
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

def match_and_ensemble(anomaly_outputs, detection_outputs, use_anomaly=False):
    """
    Match outputs from Anomaly detection and YOLO, prioritizing YOLO detections.
    YOLO detections with class=1 (boat) are included in the output regardless of confidence score.
    Duplicate detections are avoided.
    """

    output = []
    processed_yolo_indices = set()  # To track already processed YOLO detections
    threshold = 50
    confidence_threshold = 0.7
    
    # First process YOLO detections
    for idx, yl_output in enumerate(detection_outputs):
        if yl_output[1] == 1:  # Include class=1 (boat)
            output.append([yl_output[2], yl_output[3], yl_output[2]+yl_output[4], yl_output[3]+yl_output[5], yl_output[6], yl_output[1]])
            processed_yolo_indices.add(idx)

    if use_anomaly:
        for a_output in anomaly_outputs:
            closest_yl_output = None
            min_distance = float('inf')

            for idx, yl_output in enumerate(detection_outputs):
                if idx in processed_yolo_indices:  # Skip already processed YOLO detection
                    continue

                distance = calculate_distance(a_output[2:6], yl_output[2:6])
                if distance < min_distance:
                    min_distance = distance
                    closest_yl_output = yl_output
                    closest_idx = idx

            if closest_yl_output and min_distance < threshold:
                output.append([closest_yl_output[2], closest_yl_output[3], closest_yl_output[2]+closest_yl_output[4], closest_yl_output[3]+closest_yl_output[5], closest_yl_output[6], closest_yl_output[1]])
                processed_yolo_indices.add(closest_idx)
            elif not closest_yl_output or min_distance >= threshold:
                if a_output[6] >= confidence_threshold:            
                    output.append([a_output[2], a_output[3], a_output[2]+a_output[4], a_output[3]+a_output[5],a_output[6], a_output[1]])

    return output




# Test the final function with new criteria
if __name__ == "__main__":
    use_anomaly = True
    anomaly_detection_output = [
        [1, 1, 1830.63, 1000.72, 20.35, 24, 0.36],
        [1, 1, 1829.35, 1001.16, 14.65, 34.63, 0.45],
        [1, 1, 1909.35, 1021.16, 22.65, 34.63, 0.15],
        [1, 1, 1749.75, 982.50, 32.33, 30.00, 0.82]
    ]

    detection_output = [
        [1, 1, 996.39, 458.72, 86.94, 134.92, 0.93],
        [1, 0, 1841.63, 1011.72, 20.43, 26.55, 0.86],
        [1, 0, 1829.35, 1001.16, 14.65, 34.63, 0.55],
        [1, 0, 1746.75, 979.50, 29.33, 25.00, 0.32]
    ]

    output = match_and_ensemble(anomaly_detection_output, detection_output, use_anomaly)
    print(output)
    plot_detections(anomaly_detection_output, detection_output, output)