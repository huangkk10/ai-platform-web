"""
Dify Benchmark Serializers

用於 Dify 跑分系統的資料序列化
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from api.models import (
    DifyConfigVersion,
    DifyBenchmarkTestCase,
    DifyTestRun,
    DifyTestResult,
    DifyAnswerEvaluation
)

User = get_user_model()


class DifyConfigVersionSerializer(serializers.ModelSerializer):
    """Dify 配置版本序列化器"""
    
    created_by_name = serializers.SerializerMethodField()
    test_run_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DifyConfigVersion
        fields = [
            'id',
            'version_name',
            'description',
            'dify_api_url',
            'dify_api_key',
            'system_prompt',
            'rag_settings',
            'model_config',
            'retrieval_mode',
            'custom_config',
            'is_active',
            'is_baseline',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'test_run_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'created_by_name', 'test_run_count']
        extra_kwargs = {
            'dify_api_key': {'write_only': True}  # API Key 不在讀取時返回
        }
    
    def get_created_by_name(self, obj):
        """獲取創建者名稱"""
        if obj.created_by:
            return obj.created_by.username
        return None
    
    def get_test_run_count(self, obj):
        """獲取測試執行次數"""
        return obj.test_runs.count()


class DifyBenchmarkTestCaseSerializer(serializers.ModelSerializer):
    """Dify 基準測試案例序列化器"""
    
    class Meta:
        model = DifyBenchmarkTestCase
        fields = [
            'id',
            'test_class_name',
            'question',
            'expected_answer',
            'answer_keywords',
            'difficulty_level',
            'evaluation_criteria',
            'notes',
            'is_active',
            'order',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DifyAnswerEvaluationSerializer(serializers.ModelSerializer):
    """Dify 答案評價序列化器"""
    
    class Meta:
        model = DifyAnswerEvaluation
        fields = [
            'id',
            'test_result',
            'score',
            'is_passed',
            'matched_keywords',
            'missing_keywords',
            'evaluation_method',
            'evaluation_details',
            'ai_feedback',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DifyTestResultSerializer(serializers.ModelSerializer):
    """Dify 測試結果序列化器"""
    
    test_case_question = serializers.CharField(source='test_case.question', read_only=True)
    test_case_expected_answer = serializers.CharField(source='test_case.expected_answer', read_only=True)
    evaluation = DifyAnswerEvaluationSerializer(read_only=True)
    
    class Meta:
        model = DifyTestResult
        fields = [
            'id',
            'test_run',
            'test_case',
            'test_case_question',
            'test_case_expected_answer',
            'dify_answer',
            'response_time',
            'tokens_used',
            'dify_message_id',
            'dify_conversation_id',
            'retrieved_documents',
            'evaluation',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DifyTestRunSerializer(serializers.ModelSerializer):
    """Dify 測試執行序列化器"""
    
    version_name = serializers.CharField(source='version.version_name', read_only=True)
    results = DifyTestResultSerializer(many=True, read_only=True)
    results_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DifyTestRun
        fields = [
            'id',
            'version',
            'version_name',
            'batch_id',
            'run_name',
            'status',
            'total_cases',
            'passed_cases',
            'failed_cases',
            'pass_rate',
            'average_score',
            'average_response_time',
            'total_tokens',
            'started_at',
            'completed_at',
            'execution_time',
            'notes',
            'created_at',
            'results',
            'results_count'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_results_count(self, obj):
        """獲取結果數量"""
        return obj.results.count()


class DifyTestRunListSerializer(serializers.ModelSerializer):
    """Dify 測試執行列表序列化器（精簡版）"""
    
    version_name = serializers.CharField(source='version.version_name', read_only=True)
    
    class Meta:
        model = DifyTestRun
        fields = [
            'id',
            'version',
            'version_name',
            'batch_id',
            'run_name',
            'status',
            'total_cases',
            'passed_cases',
            'pass_rate',
            'average_score',
            'started_at',
            'completed_at',
            'execution_time',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DifyBenchmarkTestCaseBulkImportSerializer(serializers.Serializer):
    """批量導入測試案例序列化器"""
    
    format = serializers.ChoiceField(choices=['json', 'csv'], default='json')
    file = serializers.FileField(required=False)
    data = serializers.ListField(required=False)
    overwrite_existing = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """驗證必須提供 file 或 data 之一"""
        if not attrs.get('file') and not attrs.get('data'):
            raise serializers.ValidationError('必須提供 file 或 data 之一')
        return attrs
