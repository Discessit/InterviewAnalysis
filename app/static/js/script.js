async function loadReports() {
    const reports = [
        '/static/reports/report1.json',
        '/static/reports/report2.json',
        '/static/reports/report3.json',
        '/static/reports/report4.json'
    ];
    const reportsContainer = document.getElementById('reports');

    for (const reportUrl of reports) {
        try {
            const response = await fetch(reportUrl);
            const report = await response.json();
            const card = document.createElement('div');
            card.className = 'col-md-6 mb-4';
            card.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Пример анализа #${reports.indexOf(reportUrl) + 1}</h5>
                        <h6>Soft Skills</h6>
                        <p><strong>Естественность:</strong> ${report.soft_skills.authenticity_naturalness.description}</p>
                        <p><strong>Раппорт:</strong> ${report.soft_skills.rapport_likeability.description}</p>
                        <h6>Целостность</h6>
                        <p><strong>Паузы:</strong> ${report.integrity.pauses_delivery.description}</p>
                        <h6>Оценки</h6>
                        <ul>
                            <li>Естественность: ${report.quantitative_scores.naturalness}</li>
                            <li>Раппорт: ${report.quantitative_scores.likeability_rapport}</li>
                            <li>Целостность: ${report.quantitative_scores.interview_integrity}</li>
                        </ul>
                        <h6>Итог</h6>
                        <p><strong>Рекомендация:</strong> ${report.summary.recommendation}</p>
                    </div>
                </div>
            `;
            reportsContainer.appendChild(card);
        } catch (error) {
            console.error('Ошибка загрузки отчета:', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', loadReports);