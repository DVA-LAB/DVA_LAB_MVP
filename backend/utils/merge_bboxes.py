import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_detections(anomaly_detections, bytetrack_detections, final_detections, image_size=(4000, 3000)):
    """
    Plots detections from anomaly detection and bytetrack on a black background image.
    Anomaly detections are plotted in red, bytetrack detections in blue, and final detections in orange.
    """
    fig, ax = plt.subplots(1, figsize=(12, 9))
    ax.set_xlim(0, image_size[0])
    ax.set_ylim(image_size[1], 0)
    ax.imshow([[0,0],[0,0]], cmap='gray', extent=[0, image_size[0], 0, image_size[1]])

    # Plot anomaly detections in red
    for det in anomaly_detections:
        box = det[3:7]
        rect = patches.Rectangle((box[0], box[1]), box[2], box[3], linewidth=1, edgecolor='red', facecolor='red', alpha=0.5)
        ax.add_patch(rect)

    # Plot bytetrack detections in blue
    for det in bytetrack_detections:
        box = det[3:7]
        rect = patches.Rectangle((box[0], box[1]), box[2], box[3], linewidth=1, edgecolor='blue', facecolor='blue', alpha=0.5)
        ax.add_patch(rect)

    # Highlight final detections in orange
    for det in final_detections:
        box = det[3:7]
        rect = patches.Rectangle((box[0], box[1]), box[2], box[3], linewidth=1, edgecolor='orange', facecolor='none')
        ax.add_patch(rect)

    plt.show()

def calculate_distance(box1, box2):
    """
    Calculate the Euclidean distance between the centers of two boxes.
    """
    center1_x, center1_y = box1[0] + box1[2] / 2, box1[1] + box1[3] / 2
    center2_x, center2_y = box2[0] + box2[2] / 2, box2[1] + box2[3] / 2
    distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5
    return distance

def sort_by_track_id(outputs):
    return sorted(outputs, key=lambda x: x[1])

def match_and_ensemble(anomaly_outputs, bytetrack_outputs, use_anomaly=False):
    """
    Corrected function to match outputs from Anomaly detection and BYTETRACK, ensuring no duplicate track_ids in a single frame.
    """
    if use_anomaly:
        ensemble_output = []
        threshold = 50  # Threshold for considering two detections as the same object
        confidence_threshold = 0.7  # Minimum confidence score to consider an anomaly detection valid
        used_track_ids = set()  # Track the used track_ids to avoid duplicates

        # Iterate through anomaly detection outputs
        for a_output in anomaly_outputs:
            closest_bt_output = None
            min_distance = float('inf')

            # Find the closest BYTETRACK output
            for bt_output in bytetrack_outputs:
                if bt_output[1] not in used_track_ids:
                    distance = calculate_distance(a_output[3:7], bt_output[3:7])
                    if distance < min_distance:
                        min_distance = distance
                        closest_bt_output = bt_output

            # Use BYTETRACK output if it's a boat and not already used
            if closest_bt_output and min_distance < threshold and closest_bt_output[2] == 1:
                ensemble_output.append(closest_bt_output)
                used_track_ids.add(closest_bt_output[1])
            elif not closest_bt_output or min_distance >= threshold:
                # Check the confidence score of the Anomaly Detection output
                if a_output[7] >= confidence_threshold:
                    ensemble_output.append(a_output)
        output = sort_by_track_id(ensemble_output)
    else:
        output = bytetrack_outputs
    return output

# Test the final function with new criteria
if __name__ == "__main__":
    use_anomaly = True
    anomaly_detection_output = [
        [1, -1, 1, 1830.63, 1000.72, 20.35, 24, 0.36, -1, -1, -1],
        [1, -1, 1, 1829.35, 1001.16, 14.65, 34.63, 0.45, -1, -1, -1],
        [1, -1, 1, 1909.35, 1021.16, 22.65, 34.63, 0.15, -1, -1, -1],
        [1, -1, 1, 1749.75, 982.50, 32.33, 30.00, 0.82, -1, -1, -1]
    ]

    bytetrack_output = [
        [1, 1, 0, 996.39, 458.72, 86.94, 134.92, 0.93, -1, -1, -1],
        [1, 2, 1, 1841.63, 1011.72, 20.43, 26.55, 0.86, -1, -1, -1],
        [1, 3, 1, 1829.35, 1001.16, 14.65, 34.63, 0.55, -1, -1, -1],
        [1, 4, 1, 1746.75, 979.50, 29.33, 25.00, 0.32, -1, -1, -1]
    ]

    ensemble_output = match_and_ensemble(anomaly_detection_output, bytetrack_output, use_anomaly)
    print(ensemble_output)
    plot_detections(anomaly_detection_output, bytetrack_output, ensemble_output)

