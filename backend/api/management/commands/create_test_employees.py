from django.core.management.base import BaseCommand
from api.models import Employee
from datetime import date


class Command(BaseCommand):
    help = '創建測試員工數據用於 Dify 知識庫查詢演示'

    def handle(self, *args, **options):
        # 清除現有的員工數據
        Employee.objects.all().delete()
        
        # 創建測試員工數據
        test_employees = [
            {
                'name': '張小明',
                'email': 'zhang.xiaoming@company.com',
                'department': '技術部',
                'position': 'Python 開發工程師',
                'skills': 'Python, Django, React, PostgreSQL, Docker, API 開發',
                'phone': '0912-345-678',
                'hire_date': date(2022, 3, 15),
                'is_active': True
            },
            {
                'name': '李美華',
                'email': 'li.meihua@company.com',
                'department': '產品部',
                'position': '產品經理',
                'skills': '產品規劃, 需求分析, Figma, Jira, 專案管理',
                'phone': '0923-456-789',
                'hire_date': date(2021, 8, 20),
                'is_active': True
            },
            {
                'name': '王大強',
                'email': 'wang.daqiang@company.com',
                'department': '技術部',
                'position': 'DevOps 工程師',
                'skills': 'Docker, Kubernetes, AWS, Jenkins, Terraform, 自動化部署',
                'phone': '0934-567-890',
                'hire_date': date(2020, 11, 10),
                'is_active': True
            },
            {
                'name': '陳小雯',
                'email': 'chen.xiaowen@company.com',
                'department': '設計部',
                'position': 'UI/UX 設計師',
                'skills': 'Figma, Adobe XD, Photoshop, 使用者體驗設計, 原型設計',
                'phone': '0945-678-901',
                'hire_date': date(2022, 6, 1),
                'is_active': True
            },
            {
                'name': '林志豪',
                'email': 'lin.zhihao@company.com',
                'department': '技術部',
                'position': '前端開發工程師',
                'skills': 'React, Vue.js, TypeScript, CSS, JavaScript, 響應式設計',
                'phone': '0956-789-012',
                'hire_date': date(2021, 12, 5),
                'is_active': True
            },
            {
                'name': '劉小玲',
                'email': 'liu.xiaoling@company.com',
                'department': '行銷部',
                'position': '數位行銷專員',
                'skills': 'Google Analytics, SEO, SEM, 社群媒體行銷, 內容行銷',
                'phone': '0967-890-123',
                'hire_date': date(2023, 1, 15),
                'is_active': True
            },
            {
                'name': '黃建國',
                'email': 'huang.jianguo@company.com',
                'department': '財務部',
                'position': '財務分析師',
                'skills': 'Excel, 財務分析, 預算規劃, SAP, 成本控制',
                'phone': '0978-901-234',
                'hire_date': date(2020, 4, 8),
                'is_active': True
            },
            {
                'name': '吳佳玲',
                'email': 'wu.jialing@company.com',
                'department': '人事部',
                'position': 'HR 專員',
                'skills': '招聘, 員工關係, 薪酬福利, 教育訓練, 勞動法規',
                'phone': '0989-012-345',
                'hire_date': date(2022, 9, 20),
                'is_active': True
            },
            {
                'name': '鄭智明',
                'email': 'zheng.zhiming@company.com',
                'department': '技術部',
                'position': '資料工程師',
                'skills': 'Python, SQL, Apache Spark, ETL, 數據分析, Machine Learning',
                'phone': '0990-123-456',
                'hire_date': date(2021, 5, 12),
                'is_active': True
            },
            {
                'name': '蔡小華',
                'email': 'cai.xiaohua@company.com',
                'department': '業務部',
                'position': '業務代表',
                'skills': '客戶關係管理, 銷售技巧, CRM, 商務談判, 市場開發',
                'phone': '0901-234-567',
                'hire_date': date(2023, 3, 8),
                'is_active': True
            }
        ]
        
        # 批量創建員工
        employees = []
        for emp_data in test_employees:
            employee = Employee(**emp_data)
            employees.append(employee)
        
        Employee.objects.bulk_create(employees)
        
        self.stdout.write(
            self.style.SUCCESS(f'成功創建 {len(test_employees)} 個測試員工數據')
        )
        
        # 顯示創建的員工資訊
        for emp in Employee.objects.all():
            self.stdout.write(f'✓ {emp.name} - {emp.department} - {emp.position}')