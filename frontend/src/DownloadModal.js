import React from 'react';
import Modal from 'react-modal';

Modal.setAppElement('#root'); // 모달을 루트 엘리먼트에 연결

const modalStyles = {
    overlay: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.5)', // 배경 어둡게
    },
    content: {
        width: '300px', // 모달의 너비
        height: '150px',
        padding: '20px',
        textAlign: 'center',
        borderRadius: '5px',
        backgroundColor: 'white', // 모달 내부 배경색
    },
};

const DownloadModal = ({ isOpen, onClose }) => {
    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={onClose}
            contentLabel="Download Modal"
            style={modalStyles} // 스타일 적용
        >
            <h2>다운로드 중</h2>
            <p>진행 중...</p>
        </Modal>
    );
};

export default DownloadModal;
