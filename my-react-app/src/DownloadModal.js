// DownloadModal.js
import React from 'react';
import Modal from 'react-modal';

Modal.setAppElement('#root'); // 모달을 루트 엘리먼트에 연결

const DownloadModal = ({ isOpen, downloadProgress, onClose }) => {
    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={onClose}
            contentLabel="Download Modal"
        >
            <h2>다운로드 중</h2>
            <p>진행 상황: {downloadProgress}% 완료</p>
            <p>예상 다운로드 시간: {calculateRemainingTime(downloadProgress)} 남음</p>
            <button onClick={onClose}>닫기</button>
        </Modal>
    );
};

export default DownloadModal;

// 예상 다운로드 시간 계산 함수
function calculateRemainingTime(progress) {
    // 100%에서 현재 진행 상황(progress)을 뺀 남은 진행 상황을 구합니다.
    const remainingProgress = 100 - progress;

    // 다운로드 속도를 예상하여 초당 진행 상황을 계산합니다.
    // 이 예제에서는 초당 2% 진행 상황으로 설정합니다.
    const progressRate = 2; // 초당 2% 진행 상황

    // 남은 진행 상황을 초당 진행 상황으로 나누어 남은 시간(초)을 구합니다.
    const remainingTimeInSeconds = remainingProgress / progressRate;

    // 남은 시간(초)을 분과 초로 변환합니다.
    const remainingMinutes = Math.floor(remainingTimeInSeconds / 60);
    const remainingSeconds = Math.round(remainingTimeInSeconds % 60);

    return `${remainingMinutes} 분 ${remainingSeconds} 초`;
}

