import React from 'react';
import Modal from 'react-modal';

Modal.setAppElement('#root'); // 모달을 루트 엘리먼트에 연결

const DownloadModal = ({ isOpen, onClose }) => {
    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={onClose}
            contentLabel="Download Modal"
        >
            <h2>다운로드 중</h2>
            <p>진행 중...</p>
            <button onClick={onClose}>닫기</button>
        </Modal>
    );
};

export default DownloadModal;