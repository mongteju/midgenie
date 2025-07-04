// js/api.js

const API_BASE_URL = 'http://localhost:5000'; // 백엔드 서버 주소 (추후 변경 가능)

async function uploadExcelFile(file) {
    const formData = new FormData();
    formData.append('excelFile', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || '파일 업로드 실패');
        }

        return await response.json();
    } catch (error) {
        console.error('Error uploading file:', error);
        throw error;
    }
}

// 필요한 다른 API 호출 함수들을 여기에 추가할 수 있습니다.
