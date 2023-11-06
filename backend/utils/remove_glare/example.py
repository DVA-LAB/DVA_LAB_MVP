from remove_glare import RGLARE
from torch.utils.data import Dataset
from torch.utils.data import DataLoader

class VideoDataset(Dataset):
    def __init__(self, video_path, transform=None):
        self.video_path = video_path
        self.pre_processor = RGLARE(video_path, queue_len=4, save=False, gamma=True)
        self.transform = transform
    def __len__(self):
        return self.pre_processor.total_frame
    def __getitem__(self, idx):
        return self.pre_processor.f_run()

if __name__ == "__main__":
    dataset = VideoDataset('short.mp4')
    video_dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)
    print("video frame:",len(video_dataloader))
    for i, data in enumerate(video_dataloader):
        print(i, data)