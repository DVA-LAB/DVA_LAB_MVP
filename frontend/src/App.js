import React, { Component } from 'react';
import './App.css';
import { Button, Modal, Alert, Spin, Space, Upload, Typography } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  FastBackwardOutlined, 
  FastForwardOutlined 
} from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;

const API_URL =  'http://0.0.0.0:8000';
const BEV_URL = 'http://localhost:8001';
// const API_URL='http://112.216.237.124:8000';
// const BEV_URL= 'http://112.216.237.124:8001';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      videoSrc: null,
      videoName: null,
      logFile: null,
      srtFile: null,
      videoPlaying: false,
      frameNumber: 0,
      addingInfo: false,
      applyFlag: false,
      points: [],
      pointColors: [],
      pointDistances: [],
      distanceInputs: [],
      allFillUpload: false,
      aiModelActive: false,
      isLoading: false,
      exportOptionsVisible: false,
      isDownloadModalOpen: false, // 모달 열림/닫힘 상태 추가
      bevImageSrc : null, //BEV image 경로 추가
      showBEV : false, // BEV 이미지 보여주기
      showDrawLineButton : false,
      startPoint: null,
      endPoint : null,
      canvasWidth: 0,
      canvasHeight: 0,
      textBoxPosition : {x:0, y:0},
      showTextBox: false,
      lines: [],
      showProgressBar: false,
      showControlButtons: false,
      showResults: false,
      displayMode: 'video',
      showWriteDistanceButton: false,
      uploadStatus: '',
      syncCompleted: false,
      preprocessChecked: false,
      infoAdded: false,
    };

    this.videoRef = React.createRef();
    this.fileInputRef = React.createRef();
    this.logFileInputRef = React.createRef();
    this.canvasRef = React.createRef();
    this.imageRef = React.createRef();
    this.clearCanvas = this.clearCanvas.bind(this);
    this.drawLine = this.drawLine.bind(this);
    this.handleReset = this.handleReset.bind(this);
    this.drawPointsAndLines = this.drawPointsAndLines.bind(this);
  }

  handleReset = async () => {
    // Check if there's any data present
    if (this.state.videoSrc || this.state.logFile || this.state.srtFile) {
      // If data is present, ask for user confirmation before resetting
      if (window.confirm('Are you sure you want to exit and reset all data?')) {
        this.setState({ isLoading: true });
        try {
          const response = await axios.delete(`${API_URL}/reset/`);
          console.log(response.data);
          // Refresh the page after successful reset
          window.location.reload();
        } catch (error) {
          console.error('Error resetting data:', error);
          alert('Failed to reset data: ' + error);
          this.setState({ isLoading: false });
        }
      }
    } else {
      // If no data is present, just refresh the page
      window.location.reload();
    }
  };
  
  

  // 모달 열기
  openDownloadModal = () => {
    this.setState({ isDownloadModalOpen: true });
  };

  // 모달 닫기
  closeDownloadModal = () => {
    this.setState({ isDownloadModalOpen: false });
  };

  // 모달 닫기
  openSavingModal = () => {
    this.setState({ isLoading: true });
  };

  // 모달 닫기
  closeSavingModal = () => {
    this.setState({ isLoading: false });
  };

  handleVideoLoaded = () => {
    const video = this.videoRef.current;
    const canvas = this.canvasRef.current;
    if (canvas && video) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      this.drawInterval = setInterval(this.drawPointsAndLines, 100);
      this.setState({ videoPlaying: false }); // 이 부분 추가
    }
  };


  // clearCanvas 함수 수정
  clearCanvas() {
    const canvas = this.canvasRef.current;

    if (canvas) {
      const context = canvas.getContext('2d');
      if (context) {
        context.clearRect(0, 0, canvas.width, canvas.height);
      } else {
        console.error("Canvas context is not available.");
      }
    } else {
      console.error("Canvas element is not available.");
    }
  }



  toggleExportOptions = () => {
    this.setState(prevState => ({ exportOptionsVisible: !prevState.exportOptionsVisible }));
  };

  saveFrame = async () => {
    const video = this.videoRef.current;

    if (video) {
      const tempCanvas = document.createElement('canvas');
      const tempContext = tempCanvas.getContext('2d');
      tempCanvas.width = video.videoWidth;
      tempCanvas.height = video.videoHeight;

      // 비디오 프레임 그리기
      tempContext.drawImage(video, 0, 0, video.videoWidth, video.videoHeight, 0, 0, tempCanvas.width, tempCanvas.height);

      // 이미지 데이터를 다운로드
      const dataUrl = tempCanvas.toDataURL('image/jpeg');

      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = `${this.state.videoFileName}_frame${this.state.frameNumber}.JPG`;
      link.click();
    }
  };

  saveVideo = () => {
    const video = this.videoRef.current;

    if (video) {
      this.openSavingModal();

      const tempCanvas = document.createElement('canvas');
      const tempContext = tempCanvas.getContext('2d');
      tempCanvas.width = video.videoWidth;
      tempCanvas.height = video.videoHeight;

      const stream = tempCanvas.captureStream(33);  // 33fps로 스트림 생성
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
      const recordedChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.state.videoFileName}_with_canvas.webm`;  // 수정된 부분
        link.click();
        URL.revokeObjectURL(url);

        this.closeSavingModal();
      };

      mediaRecorder.start();

      let frameNumber = 0;
      const drawFrame = () => {
        if (frameNumber < video.duration * 33) {  // 33fps 기준
          video.currentTime = frameNumber / 33;
          video.onseeked = () => {
            tempContext.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
            tempContext.drawImage(video, 0, 0, video.videoWidth, video.videoHeight, 0, 0, tempCanvas.width, tempCanvas.height);
            frameNumber++;
            requestAnimationFrame(drawFrame);
          };
        } else {
          mediaRecorder.stop();
        }
      };

      drawFrame();
    }
  };

  // 파일 업로드 핸들러
  handleFileUpload = async (file) => {
    this.setState({
        // Reset states before upload
        videoFileName: null,
        videoSrc: null,
        // logFile: null,
        videoPlaying: false,
        frameNumber: 0,
        addingInfo: false,
        points: [],
        pointColors: [],
        pointDistances: [],
        distanceInputs: [],
        allFillUpload: false,
        aiModelActive: false,
        exportOptionsVisible: false,
        isDownloadModalOpen: false,
        applyFlag: false,
        lastVideoFilename: null,
        uploadStatus: 'saving',
        isLoading: true,
    });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('preprocess', this.state.preprocessChecked ? 1:0);


    try {
      const response = await axios.post(`${API_URL}/video/`, formData);


      console.log(response.data);
      if (response.data && response.data.filename) {
        this.setState({
          uploadStatus: 'parsing',
          videoFileName: response.data.filename,
        }, () => {
          this.fetchAndLoadVideo();
        });
      }
    } catch (error) {
        console.error('Error uploading file:', error);
        this.setState({
          uploadStatus: '',
          isLoading: false,
        });
    }
};

fetchAndLoadVideo = async () => {

  this.setState({
    uploadStatus: 'loading',
    // isLoading: true,
  });

  try {
      const response = await axios.get(`${API_URL}/video/`, { responseType: 'blob' });
      if (response.data) {
          const videoBlob = response.data;
          const videoUrl = URL.createObjectURL(videoBlob); // Create a URL for the video Blob
          this.setState({
              videoSrc: videoUrl,
              uploadStatus: 'saved',
              // isLoading: false,
          }, () => {
              this.loadVideo();
          });
      }
  } catch (error) {
      console.error('Error fetching video:', error);
      this.setState({
        uploadStatus: '',
        isLoading: false,
      });
  }
};



// 비디오 파일 로드
loadVideo = () => {
  const { videoSrc } = this.state;
  if (videoSrc) {
    console.log("Loading video:",videoSrc);
    this.videoRef.current.src = videoSrc;
    this.videoRef.current.load();
    this.videoRef.current.addEventListener('loadeddata', () => {
      this.videoRef.current.currentTime = 0;
      this.setState({ 
        videoPlaying: false,
        uploadStatus: '',
        isLoading: false,
       });
    });
  }
};


  handleCsvFileUpload = async (file) => {
    if (file) {
        // Update state to indicate file is being processed
        this.setState({ logFile: file, isLoading: true });

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(`${API_URL}/csv/`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            console.log(response.data);
            // Handle any additional state updates or actions on successful upload
            this.setState({ isLoading: false });

        } catch (error) {
            console.error('Error uploading CSV file:', error);
            // Handle errors and update state accordingly
            this.setState({ isLoading: false });
        }
    }
  };

  handleSrtFileUpload = async (file) => {
    if (file) {
        this.setState({ srtFile: file, isLoading: true });

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(`${API_URL}/srt/`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            console.log(response.data);
            this.setState({ isLoading: false });
        } catch (error) {
            console.error('Error uploading SRT file:', error);
            this.setState({ isLoading: false });
        }
    }
};


  // 비디오 재생/일시정지 토글
  togglePlayPause = () => {
    const { videoPlaying } = this.state;
    if (videoPlaying) {
      this.videoRef.current.pause();
    } else {
      this.videoRef.current.play();
      // 비디오 재생 시 pointDistances와 points 배열을 비웁니다.
      this.setState(() => {
        return {
          addingInfo: false,
          pointDistances: [],
          points: [],
        };
      }, () => {
        // 상태 업데이트 후에 캔버스를 지우고 점과 선을 다시 그립니다.
        this.clearCanvas();
        this.drawPointsAndLines();
      });
    }
    this.setState({ videoPlaying: !videoPlaying });
  };

  // 현재 프레임 번호 업데이트
  updateFrameNumber = () => {
    const { videoSrc } = this.state;
    if (videoSrc) {
      this.setState({ frameNumber: Math.floor(this.videoRef.current.currentTime * 30) }); // 30fps 기준
    }
  };

  syncFile = async () => {
    this.setState({ isLoading: true, syncCompleted: false });
  
    try {
      const response = await axios.post(`${API_URL}/sync/`);
      console.log(response.data);
      if(response.status===200){
        alert("Synchronized csv file successfully!");
      };
      // Update the syncCompleted state to true when the sync is done
      this.setState({ syncCompleted: true });
      // Optionally, display a success message or handle UI updates
    } catch (error) {
      console.error('Error during file synchronization:', error);
      alert('Failed to sync files: ' + error);
      // Keep syncCompleted as false if there's an error
    } finally {
      this.setState({ isLoading: false });
    }
  };
  
  

  // 추가 정보 입력 모드 활성화/비활성화 토글
  toggleAddingInfo = () => {
    this.setState(prevState => ({
      addingInfo: !prevState.addingInfo
      // Removed the logic to reset points and pointDistances
    }));
  };
  

//   captureAndSendFrame = async () => {
//     const { lastVideoFilename } = this.state;
//     const video = this.videoRef.current;

//     // Capture the current frame of the video
//     const canvas = document.createElement('canvas');
//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;
//     const ctx = canvas.getContext('2d');
//     ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

//     // Convert canvas to Blob
//     const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
//     const file = new File([blob], `frame-${Date.now()}.jpg`, { type: 'image/jpeg' });

//     const formData = new FormData();
//     formData.append('file', file);

//     try {
//         const response = await axios.post(`http://localhost:8000/bev/${lastVideoFilename}`, formData, {
//             headers: {
//                 'Content-Type': 'multipart/form-data',
//             },
//         });
//         if (response.data && response.data.framePath) {
//             const framePath = response.data.framePath.split('/').pop();
//             const getImageUrl = `http://localhost:8000/extracted_frames/${framePath}`;
//             console.log(getImageUrl);
//             return getImageUrl;
//         }
//     } catch (error) {
//         console.error('Error sending frame for BEV conversion:', error);
//     }
// };

  captureAndSendFrame = async () => {
    const { frameNumber } = this.state; // Assuming frameNumber is stored in state

    try {
      const response = await axios.get(`${API_URL}/frame/${frameNumber}`, { responseType: 'blob' });
      if (response.data) {
        const frameBlob = response.data;
        const frameUrl = URL.createObjectURL(frameBlob); // Create a URL for the frame Blob
        console.log(frameUrl);
        return frameUrl;
      }
    } catch (error) {
      console.error('Error fetching frame:', error);
    }
  };


  toggleBEVView = async () => {
    const { showBEV, frameNumber, videoFileName } = this.state;
    const parts = videoFileName.split('.');
  
    // Remove the last part (the extension)
    const fileNameWithoutExtension = parts.slice(0, -1).join('.');
    const frameNumberPadded = frameNumber.toString().padStart(5, '0'); // Pad frame number with leading zeros
    const framePath = `/home/dva4/dva/backend/test/frame_origin/${fileNameWithoutExtension}_${frameNumberPadded}.jpg`; 
    const csvPath = `/home/dva4/dva/backend/test/sync_csv/sync_log.csv`;
    const dstDir = "api/services/Orthophoto_Maps/Data/result"; // Destination directory
  
    const formatObjectsArray = (lastEntry) => {
      if (!lastEntry) return null;
  
      const { point1, point2 } = lastEntry;
      return [null, null, null, point1.x, point1.y, point2.x, point2.y, null, -1, -1, -1];
    };
  
    const lastEntry = this.state.pointDistances[this.state.pointDistances.length - 1];
    const objects = formatObjectsArray(lastEntry); 
  
    if (!objects) {
      console.error("No point distances available for BEV conversion");
      this.setState({ isLoading: false });
      return;
    }
  
    const payload = {
      frame_num: frameNumber,
      frame_path: framePath,
      csv_path: csvPath,
      objects: objects,
      realdistance: lastEntry.distance,
      dst_dir: dstDir,
    }
    console.log(payload);
  
    if (!showBEV && this.state.infoAdded) {
      this.setState({ isLoading: true });
  
      try {
        const response = await axios.post(`${BEV_URL}/bev1`, payload, {
            responseType: 'blob',  // Set response type to 'blob' for file download
        });
    
        if (response.data) {
            const blob = new Blob([response.data], { type: 'image/png' });
            const bevImageSrc = URL.createObjectURL(blob);
    
            this.setState({
                showBEV: true,
                bevImageSrc,  // Use the created Blob URL here
                isLoading: false,
            });
        } else {
            console.error("BEV conversion failed");
            this.setState({ isLoading: false });
        }
    } catch (error) {
        console.error("Error during API call:", error);
        this.setState({ isLoading: false });
    }
    } else {
      this.setState({
        showBEV: false,
        videoSrc: `${API_URL}/video/`
      }, () => {
        this.loadVideo();
      });
    }
  };
  
  
  
  
  
  // enableDrawing = () => {
  //   this.setState({ 
  //     drawingLine: !this.state.drawingLine,
  //     startPoint: null,
  //     endPoint: null,
  //     points: [], // reset points if you're starting a new line
  //   });
  // };

  
  

  handleMouseDown = (event) => {
    
    event.stopPropagation();
    
    const canvas = this.canvasRef.current;
    if (!canvas || !this.state.addingInfo) return;

    // if(!this.state.addingInfo) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;

    const newPoint = { x, y };

    console.log("New Point:", newPoint);

    this.drawPoint(newPoint, canvas); // Draw the point

    this.setState(prevState => {
      const newPoints = [...prevState.points, newPoint];
      const showWriteDistanceButton = newPoints.length===2;
      
      console.log("Points after adding new point:", newPoints);
      if (newPoints.length === 2) {
        // If two points are selected, draw line and reset points
        this.drawLine(newPoints[0], newPoints[1]);
        // const distance = prompt("Enter the distance (m):");
        // const distance = prompt("Enter the distance (m):");
        // this.drawLabel(newPoints[0], newPoints[1], distance);

        return { 
          points: newPoints,
          showWriteDistanceButton,
          // showTextBox: true,
          // textBoxPosition: {x:screenX,y: screenY} 
          // pointDistances: [...prevState.pointDistances, distance],
        }; // reset points
      }
      console.log(newPoints,);
      return { points: newPoints };
    });
  };

drawPoint = (point, canvas) => {
  // const canvas = this.canvasRef.current;
  const ctx = canvas.getContext('2d');

  ctx.beginPath();
  ctx.arc(point.x, point.y, 1, 0, 2 * Math.PI, true); // Draw a circle
  ctx.fillStyle = '#FF0000';
  ctx.fill();
};

drawLine = (startPoint, endPoint) => {
  const canvas = this.canvasRef.current;
  const ctx = canvas.getContext('2d');

  ctx.beginPath();
  ctx.moveTo(startPoint.x, startPoint.y);
  ctx.lineTo(endPoint.x, endPoint.y);
  ctx.stroke();
};

handleDistanceInput = (event) => {
  const distance = event.target.value;
  if (distance && !isNaN(distance)) {
    this.setState(prevState => {
      const { points } = prevState;
      if (points.length >= 2) {
        const lastIndex = points.length - 1;
        this.drawLabel(points[lastIndex - 1], points[lastIndex], distance);
        const newEntry = {
          point1: points[lastIndex - 1],
          point2: points[lastIndex],
          distance: parseFloat(distance)
        };
        return { 
          pointDistances: [...prevState.pointDistances, newEntry], 
          infoAdded: true,
          points: [] // Clear points after adding distance
        };

      }
      return null;
    });
  }
};


drawLabel = (startPoint, endPoint, text) => {
  const canvas = this.canvasRef.current;
  const context = canvas.getContext('2d');

  const midX = (startPoint.x + endPoint.x) / 2;
  const midY = (startPoint.y + endPoint.y) / 2;

  // Adjust the size of the label box
  const labelWidth = 20; // reduced from 150
  const labelHeight = 10; // reduced from 40

  // Draw label background with reduced size
  // context.globalAlpha = 0.5;
  context.fillStyle = 'transparent';
  context.fillRect(midX - labelWidth / 2, midY - labelHeight / 2, labelWidth, labelHeight);

  // Draw label text with smaller font
  context.fillStyle = 'red';
  context.font = "8px Arial"; // reduced font size
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText(`${text}m`, midX, midY);
};


  handleMouseMove = (e) => {
    if (!this.state.isDrawing) return;
  
    const canvas = this.canvasRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const lastPoint = this.state.lastPoint;
  
    ctx.beginPath();
    ctx.moveTo(lastPoint.x, lastPoint.y);
    ctx.lineTo(x, y);
    ctx.stroke();
  
    this.setState({ lastPoint: { x, y } });
  };
  
  handleMouseUp = () => {
    this.setState({ isDrawing: false, lastPoint: null });
  };
  


  // calculateDistance 함수 수정
  calculateDistance = (pointIndex) => {
    const { points } = this.state;
    console.log(points);
    const point1 = points[pointIndex - 1];
    const point2 = points[pointIndex];

    const distancePixels = Math.sqrt((point2.x - point1.x) ** 2 + (point2.y - point1.y) ** 2);

    // Prompt for distance input after drawing points and lines
    setTimeout(() => {
      const distanceMeters = parseFloat(prompt(`Enter distance between point ${pointIndex - 1} and point ${pointIndex} in meters:`));
      if (!isNaN(distanceMeters)) {
        const pointDistances = [...this.state.pointDistances, { meters: distanceMeters, pixels: distancePixels }];
        this.setState({ pointDistances }, () => {
          // 상태 업데이트 후에 점과 선을 다시 그립니다.
          this.drawPointsAndLines();
        });
      } else {
        alert('Invalid input. Please enter a valid number for the distance.');
      }
    }, 0);
  };
  applyGSD = () => {
    console.log('applyGSD');
    this.setState({ applyFlag: true });
    this.toggleAddingInfo();
  }
  // << 5 seconds backward 버튼 클릭 핸들러
  skipBackward = () => {
    this.videoRef.current.currentTime -= 5;
    this.setState(() => {
      return {
        addingInfo: false,
        pointDistances: [],
        points: [],
      };
    }, () => {
      // 상태 업데이트 후에 캔버스를 지우고 점과 선을 다시 그립니다.
      this.clearCanvas();
      this.drawPointsAndLines();
    });
  };

  // >> 5 seconds forward 버튼 클릭 핸들러
  skipForward = () => {
    this.videoRef.current.currentTime += 5;
    this.setState(() => {
      return {
        addingInfo: false,
        pointDistances: [],
        points: [],
      };
    }, () => {
      // 상태 업데이트 후에 캔버스를 지우고 점과 선을 다시 그립니다.
      this.clearCanvas();
      this.drawPointsAndLines();
    });
  };

  // Run AI Model 버튼 클릭 핸들러
  runAIModel = async () => {
    this.setState({aiModelActive:true, showProgressBar: true, showControlButtons: true });

    setTimeout(()=>{
      this.setState({ showProgressBar: false });
    }, 30000)

    // Prepare the payload for the API request
    const payload = {
        frame_path: "/home/dva4/dva/backend/test/frame_origin"/* path to the frame images */,
        detection_save_path:"/home/dva4/dva/backend/test/model/detection/result" /* path where detection results should be saved */,
        sliced_path: "/home/dva4/dva/backend/test/model/sliced"/* path for sliced images, if applicable */,
        output_merge_path: "/home/dva4/dva/backend/test/model/merged"/* path for merged output */,
        // ... include other necessary fields based on your API's requirements
    };

    //완성되면 아래 코드로 inference 연결하기!

    // try {
    //     // Make the API call
    //     const response = await axios.post(`${API_URL}/inference`, payload);

    //     if (response.status === 200) {
    //         // Handle successful response
    //         console.log("Model inference successful:", response.data);
    //         this.setState({aiModelActive: false, showResults: true})

    //         // Update your application state as necessary
    //         // For example, if response contains a path to a result file, update the state to reflect this
    //     } else {
    //         // Handle non-successful responses
    //         console.error("Model inference failed with status:", response.status);
    //         // Update your application state as necessary
    //     }
    // } catch (error) {
    //     console.error("Error during model inference:", error);
    //     // Update your application state to reflect the error
    // } finally {
    //     // Update state to indicate that the AI model has finished running
    //     this.setState({aiModelActive: false, showProgressBar: false});
    // }
  
    
  };


  

  // 비디오를 미리보기로 보여주는 함수
  reLoadVideo = async (newVideoPath) => {
    // 모달 열기
    this.openDownloadModal();
    // Set the initial state
    this.setState({ videoPlaying: false });

    try {
      // Now, you can replace the video source with the downloaded video URL
      const video = this.videoRef.current;
      if (video) {
        video.src = newVideoPath;
        video.crossOrigin = "anonymous"; // CORS 설정
        video.load();
        video.addEventListener('loadeddata', () => {
          video.currentTime = 0;
          this.setState({ videoPlaying: false });
        });

        this.closeDownloadModal();
      }
    } catch (error) {
      console.error('Error downloading and saving video:', error);
      this.closeDownloadModal();
    }
  };

  // 점과 선 그리기 함수
  drawPointsAndLines() {
    const canvas = this.canvasRef.current;
    if (!canvas) {
      console.error("Canvas element is not available.");
      return;
    }

    const context = canvas.getContext('2d');
    if (!context) {
      console.error("Canvas context is not available.");
      return;
    }

    const { points, pointColors, addingInfo, pointDistances } = this.state;

    context.clearRect(0, 0, canvas.width, canvas.height); // 캔버스 지우기

    for (let i = 0; i < points.length; i++) {
      // 현재 점의 색상을 설정합니다.
      context.fillStyle = pointColors[i % 2 === 0 ? i : i - 1];
      context.beginPath();
      context.arc(points[i].x, points[i].y, 10, 0, Math.PI * 2);
      context.fill();

      // 짝수 인덱스일 때 선을 그립니다.
      if (i % 2 === 1 && i > 0) {
        // 이전 점의 색상을 사용하여 선의 색상을 설정합니다.
        context.strokeStyle = pointColors[i - 1];
        context.lineWidth = 2;
        context.beginPath();
        context.moveTo(points[i - 1].x, points[i - 1].y);
        context.lineTo(points[i].x, points[i].y);
        context.stroke();

        // 선에 텍스트를 추가합니다.
        // 이전 점의 색상을 사용하여 텍스트의 색상을 설정합니다.
        context.fillStyle = 'white'; // 배경색을 흰색으로 설정
        context.fillRect(
          (points[i - 1].x + points[i].x) / 2 - 75,
          (points[i - 1].y + points[i].y) / 2 - 20,
          150,
          40
        );

        context.fillStyle = 'black'; // 글씨색을 검정색으로 설정
        context.font = "20px Arial";
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        // 선의 중간에 라벨을 추가합니다.
        const labelText = pointDistances[(i - 1) / 2]
          ? `line${(i + 1) / 2} = ${pointDistances[(i - 1) / 2].meters}(m)`
          : `line${(i + 1) / 2}`;

        context.fillText(labelText, (points[i - 1].x + points[i].x) / 2, (points[i - 1].y + points[i].y) / 2);
      }
    }
  }

  seeResults = async () => {

    const formData = {
      // 서버에 연결할때는 위에꺼 쓰기
      // "log_path": "/home/dva4/dva/backend/test/sync_csv",
      // "input_dir": "/home/dva4/dva/backend/test/frame_origin",
      // "output_video": "/home/dva4/dva/backend/test/result/result.mp4",
      // "bbox_path": "/home/dva4/dva/backend/test/model/tracking/result.txt",
      // "set_merged_dolphin_center": false,
      // "video_path": ""/home/dva4/dva/backend/test/video_origin"
      "log_path": "/Users/dongwookim/DVA_LAB/backend/test/sync_csv",
      "input_dir": "/Users/dongwookim/DVA_LAB/backend/test/frame_origin",
      "output_video": "/Users/dongwookim/DVA_LAB/backend/test/result/result.mp4",
      "bbox_path": "/Users/dongwookim/DVA_LAB/backend/test/model/tracking/result.txt",
      "set_merged_dolphin_center": false,
      "video_path": "/Users/dongwookim/DVA_LAB/backend/test/video_origin"
    }
    
    const response = await axios.post(`${API_URL}/visualize/`, formData);

    
    this.setState({ 
      showResults: true,
      videoSrc: `${API_URL}/video/`,
     },()=>{
      this.loadVideo();
     });
     console.log(this.state.videoSrc)
  };

  toggleDisplayMode =()=> {
    this.setState(prevState => ({
      displayMode: prevState.displayMode === 'video' ? 'image' : 'video'
    }));
  }

  // 렌더링
  render() {
    const ProgressBar = () => (
      <div style={{ width: '100%', backgroundColor: '#ccc', height: '20px', position: 'absolute', top: 0 }}>
        <div style={{ width: '50%', /* Dynamic based on progress */ backgroundColor: 'blue', height: '100%' }}></div>
      </div>
    );
    
    // 화면 높이 구하기
    const screenHeight = window.innerHeight;

    // 비디오 스타일 정의
    const videoStyle = {
      width: '100%',
      height: '80%',
      position: 'relative',
      zIndex: 0
    };

    const canSeeResults = this.state.points.length / 2 === this.state.pointDistances.length &&
                          this.state.points.length >= 2;

    const { logFile, srtFile, videoSrc, videoPlaying, frameNumber, addingInfo, isLoading, applyFlag, allFillUpload, aiModelActive, showBEV, showDrawLineButton, points, showResults, uploadStatus, syncCompleted } = this.state;

    if (showResults) {
      return (
        <div className="App" style={{ height: screenHeight + 'px', position: 'relative' }}>
          <Button
            type="text"
            onClick={this.handleReset}
            style={{ 
              fontSize: '2rem', // Adjust the size as needed to match a title
              fontWeight: 'bold',
              margin: 0,
              padding: 0,
              border: 'none',
              boxShadow: 'none',
              cursor: 'pointer',
              background: 'none'
            }}
          >
            Drone Video Analysis for MARC
          </Button>

          <Space direction="vertical">

          
          {/* Toggle Button */}
          <Button onClick={this.toggleDisplayMode}>
            {this.state.displayMode === 'video' ? 'Show Image' : 'Show Video'}
          </Button>
    
          {/* Conditional Rendering Based on Display Mode */}
          {this.state.displayMode === 'video' ? (
            <div>
            <video
              ref={this.videoRef}
              onError={(e)=> console.error("Error Loading video:", e)}
              crossOrigin='anonymous'

              style={{
                width: '100%',
                height: '80%',
                position: 'relative',
                zIndex: 0,
                
              }}

              onTimeUpdate={this.updateFrameNumber}
              // other video properties
            >
               <source src={this.state.videoSrc} type="video/mp4"/>
            </video>
             
            <Space direction="vertical" style={{ alignItems: 'center' }}>
            <div style={{ fontSize: '30px' }}>
              {videoSrc && <p>Frame: {frameNumber}</p>}
            </div>
            <Space>
              <Button onClick={this.skipBackward} icon={<FastBackwardOutlined />} />
              <Button onClick={this.togglePlayPause} icon={videoPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />} />
              <Button onClick={this.skipForward} icon={<FastForwardOutlined />} />
            </Space>
          </Space> 
          </div>
          ) : (
            <img src="result.png" alt="Results" style={{ ...videoStyle, objectFit: 'contain' }} />
          )}
          </Space>
        </div>
        
      );
    }
    
    

    return (
      <div className="App" style={{ height: screenHeight + 'px', position: 'relative' }}>
        
        {this.state.showProgressBar && <div className="loading-bar"></div>}
        
        <Space direction="vertical" style={{ marginTop: '40px' }}>
        <Button
            type="text"
            onClick={this.handleReset}
            style={{ 
              fontSize: '2rem', // Adjust the size as needed to match a title
              fontWeight: 'bold',
              margin: 0,
              padding: 0,
              border: 'none',
              boxShadow: 'none',
              cursor: 'pointer',
              background: 'none'
            }}
          >
            Drone Video Analysis for MARC
          </Button>
         
          <div className='video-bev-container' style={{ position: 'relative', ...videoStyle }}>
            {/* Show loading indicator and status messages when isLoading is true */}
            
            {this.state.isLoading && (
              <div style={{
                position: 'absolute', 
                top: '50%', 
                left: '50%', 
                transform: 'translate(-50%, -50%)', 
                textAlign: 'center'
              }}>
                <div className="loader" style={{ margin: '0 auto' }}></div>
                {this.state.uploadStatus === 'saving' && <div style={{ marginTop: '20px' }}>영상을 저장하고 프레임을 파싱 중입니다.<br/>시간이 오래 걸릴 수 있습니다.</div>}
                {this.state.uploadStatus === 'loading' && <div style={{ marginTop: '20px' }}>Loading video...</div>}
              </div>
            )}
            
            {!showBEV&&(<video
              ref={this.videoRef}
              crossOrigin='anonymous'
              src={this.state.videoSrc} // Set the src attribute to use videoSrc from the state
              onTimeUpdate={this.updateFrameNumber}
              style={videoStyle}
              // onLoadedData={this.handleVideoLoaded}
            />)}

{!videoPlaying && !showBEV && (
        <canvas
          ref={this.canvasRef}
          onMouseDown={this.handleMouseDown}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            zIndex: 1,
          }}
        />
      )}

              
          {showBEV && (
                  <img
                    src={this.state.bevImageSrc}
                    alt="Bird's Eye View"
                    ref={this.imageRef}
                    style={{ width: '100%', height: '100%' }}
                  />
                )}
            


              {points.length >= 2 && points.length % 2===0 && (
            <input
                type="number"
                min="0"
                placeholder="Enter distance (m)"
                onBlur={this.handleDistanceInput}
                style={{ position: 'absolute', left: '10px', top: '10px', zIndex:2 }} // Adjust position as needed
            />
        )}
          </div>
          <Space>
            {this.videoRef.current && applyFlag && (
              <>
                <Button type="primary" onClick={this.saveFrame}>Save Frame</Button>
                <div>
                  {isLoading && (
                    <Modal
                      title="동영상 저장 중..."
                      open={isLoading}
                      footer={null}
                      closable={false}
                    >
                      <p>저장 작업이 진행 중입니다. 잠시만 기다려주세요.</p>
                    </Modal>
                  )}
                  {!isLoading && <Button type="primary" onClick={this.saveVideo}>Save Video</Button>}
                </div>
              </>
            )} 
            
          </Space>
          
          {/* {showBEV && this.state.pointDistances.length > 0 && (
              
            )} */}
          <Space style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Space style={{ display: 'flex', flexDirection: 'row', alignItems: 'center' }}>
            {syncCompleted && !showBEV && !this.state.aiModelActive && (
              <div>
                <Button style={{ backgroundColor: 'red', color: 'white' }} onClick={this.runAIModel}>
                  AI 모델 실행
                </Button>
              </div>
            )}
            {logFile && srtFile && !showBEV && !this.state.aiModelActive && (
            <div>
              <Button 
                style={{ backgroundColor: 'red', color: 'white' }} 
                onClick={this.syncFile}
                disabled={this.state.isLoading} // Disable the button when loading
              >
                {this.state.syncCompleted ? '싱크 다시 맞추기' : '로그 파일 싱크 맞추기'}
              </Button>
            </div>
          )}

            </Space>
            <div>
            {/* ... existing JSX elements */}
            {uploadStatus === ''&& !this.state.aiModelActive && (
            <div>
            <input
              type="checkbox"
              checked={this.state.preprocessChecked}
              onChange={e => this.setState({ preprocessChecked: e.target.checked })}
            />
            <label>빛 반사 방지 모듈을 적용하시겠어요?<br/></label>
            <label>영상 업로드 전 체크해주세요.</label>
            </div>)}
            
            </div>
           

{/* ... rest of the JSX elements for file upload and other controls */}


            {/* Control Buttons */}
            {this.state.showControlButtons && !showBEV && (
            <Space direction="vertical" style={{ alignItems: 'center' }}>
              <div style={{ fontSize: '30px' }}>
                {videoSrc && <p>Frame: {frameNumber}</p>}
              </div>
              <Space>
                <Button onClick={this.skipBackward} icon={<FastBackwardOutlined />} />
                <Button onClick={this.togglePlayPause} icon={videoPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />} />
                <Button onClick={this.skipForward} icon={<FastForwardOutlined />} />
              </Space>
            </Space>
          )}

          </Space>


          <div>
            {this.state.infoAdded && !videoPlaying && videoSrc &&  this.state.showControlButtons && (
            <Button type="primary" onClick={this.toggleBEVView}>
              {showBEV ? '동영상으로 돌아가기' : 'BEV 전환하기'}
            </Button>
            )}

            {/* {showDrawLineButton && (
              <Button type="primary" onClick={this.handleMouseDown}>Draw Line</Button>
              )
            } */}
            {!showBEV && this.state.syncCompleted&& aiModelActive && !videoPlaying && videoSrc && (
              <Button onClick={this.toggleAddingInfo}>{addingInfo ? '거리 정보 추가 마치기' : '거리 정보 추가하기'}</Button>
            )}
            {/* {
              lines.map((line,index)=>
              <input 
                key={index}
                type="text" 
                placeholder="Real distance (m)" 
                style={{ 
                  position: 'absolute', 
                  left: `${line.textBoxPosition.x}px`, // These are relative to the parent div
                  top: `${line.textBoxPosition.y}px`, // These are relative to the parent div
                  zIndex: 2,
                }} 
                />
                )} */}
          </div>
          {!aiModelActive && (<Space direction="vertical">
            <Space>
              {/* Conditional rendering of status messages */}
              

               {/* Conditional rendering of the Upload component */}
              {uploadStatus === '' && ( // Only show the upload button if there's no ongoing process
                <Upload
                  showUploadList={false}
                  accept=".mp4,.mov"
                  customRequest={({ file }) => this.handleFileUpload(file)}
                >
                  {videoSrc ? <Button>다른 영상 업로드</Button> : <Button>영상 업로드</Button>}
                </Upload>
              )}
              <Upload
                showUploadList={false}
                accept=".csv"
                customRequest={({ file }) => this.handleCsvFileUpload(file)}
              >
                {logFile ? <Button>로그 파일 재업로드</Button> : <Button>로그 파일 업로드(.csv)</Button>}
              </Upload>
              <Upload
                showUploadList={false}
                accept=".srt"
                customRequest={({ file }) => this.handleSrtFileUpload(file)}
              >
                {srtFile ? <Button>SRT 파일 재업로드</Button> : <Button>SRT 파일 업로드</Button>}
              </Upload>
              {/* {allFillUpload && <Button onClick={this.runAIModel}>Run AI Model</Button>} */}

            </Space>
            
            
          </Space>)}
          <div>
          {aiModelActive && (
          <Button type="primary" onClick={this.seeResults}>
            결과 확인하러 가기!
          </Button>
        )}
          </div>
          {/* <div>
            {this.state.pointDistances.map((distance, index) => (
              <p key={index}>Distance {index + 1}: {distance.meters} meters ({distance.pixels.toFixed(3)} pixels)</p>
            ))}
          </div> */}
        </Space>
      </div>
    );

  }
}

export default App;
