// js/main.js

document.addEventListener('DOMContentLoaded', () => {
    const excelFileInput = document.getElementById('excelFile');
    const uploadButton = document.getElementById('uploadButton');
    const uploadStatus = document.getElementById('uploadStatus');
    const resultsSection = document.getElementById('results-section');
    const totalApplicantsDiv = document.getElementById('totalApplicants');
    const studentRankDiv = document.getElementById('studentRank');

    uploadButton.addEventListener('click', async () => {
        const file = excelFileInput.files[0];
        if (!file) {
            uploadStatus.textContent = '파일을 선택해주세요.';
            uploadStatus.style.color = 'red';
            return;
        }

        uploadStatus.textContent = '파일 업로드 중...';
        uploadStatus.style.color = 'orange';

        try {
            const result = await uploadExcelFile(file); // api.js의 함수 호출
            uploadStatus.textContent = '파일 업로드 성공!';
            uploadStatus.style.color = 'green';

            // 결과 표시
            totalApplicantsDiv.textContent = `총 지원자 수: ${result.total_applicants}명`;
            studentRankDiv.textContent = `우리 학생 예상 석차: ${result.student_rank}등 (합격 가능성: ${result.admission_probability}%)`;
            resultsSection.style.display = 'block';

        } catch (error) {
            uploadStatus.textContent = `파일 업로드 실패: ${error.message}`;
            uploadStatus.style.color = 'red';
            resultsSection.style.display = 'none';
        }
    });
});
