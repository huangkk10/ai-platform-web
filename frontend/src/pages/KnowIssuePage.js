import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Tag, 
  Space, 
  Typography,
  AutoComplete,
  message,
  Upload,
  Image
} from 'antd';
import { 
  DatabaseOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  UploadOutlined,
  PictureOutlined,
  EyeOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const { Title } = Typography;
const { Option } = Select;

const KnowIssuePage = () => {
  const { user, isAuthenticated, loading: authLoading, initialized } = useAuth();
  const [issues, setIssues] = useState([]);
  const [filteredIssues, setFilteredIssues] = useState([]);
  const [testClasses, setTestClasses] = useState([]);
  const [selectedTestClass, setSelectedTestClass] = useState(null);
  const [selectedFormTestClass, setSelectedFormTestClass] = useState(null);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewIssue, setPreviewIssue] = useState(null);
  const [editingIssue, setEditingIssue] = useState(null);
  const [form] = Form.useForm();
  
  // 圖片上傳相關狀態
  const [imageFileList, setImageFileList] = useState([]);
  const [imageModalVisible, setImageModalVisible] = useState(false);
  const [currentImageSrc, setCurrentImageSrc] = useState('');
  
  // 自動完成選項
  const [autoCompleteOptions, setAutoCompleteOptions] = useState({
    testVersions: [],
    projects: [],
    issueTypes: [],
    statuses: [],
    jiraNumbers: []
  });

  // 處理表單中測試類別的選擇
  const handleFormTestClassChange = (testClassId) => {
    const selectedClass = testClasses.find(cls => cls.id === testClassId);
    setSelectedFormTestClass(selectedClass);
  };

  // 圖片上傳處理函數
  const handleImageUpload = ({ fileList }) => {
    // 限制最多 5 張圖片
    const limitedFileList = fileList.slice(-5);
    setImageFileList(limitedFileList);
  };

  // 圖片預覽函數
  const handleImagePreview = (file) => {
    if (file.url || file.preview) {
      setCurrentImageSrc(file.url || file.preview);
      setImageModalVisible(true);
    }
  };

  // 圖片上傳前的驗證
  const beforeUpload = (file) => {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('只能上傳圖片檔案！');
      return false;
    }
    
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('圖片大小必須小於 5MB！');
      return false;
    }
    
    return false; // 返回 false 以阻止自動上傳，由表單提交時統一處理
  };

  // 將編輯時的圖片轉換為文件列表格式
  const convertExistingImagesToFileList = (issue) => {
    const fileList = [];
    if (issue.image_urls && issue.image_urls.length > 0) {
      issue.image_urls.forEach((url, index) => {
        if (url) {
          fileList.push({
            uid: `existing-${index}`,
            name: `image${index + 1}.jpg`,
            status: 'done',
            url: url,
            isExisting: true // 標記為現有圖片
          });
        }
      });
    }
    return fileList;
  };

  // 處理測試類別過濾
  const handleTestClassFilter = (testClassId, skipSave = false) => {
    setSelectedTestClass(testClassId);
    
    // 保存選擇到 localStorage（除非明確跳過保存）
    if (!skipSave) {
      if (testClassId) {
        console.log('保存測試類別選擇到 localStorage:', testClassId);
        localStorage.setItem('selectedTestClass', testClassId.toString());
      } else {
        console.log('從 localStorage 移除測試類別選擇');
        localStorage.removeItem('selectedTestClass');
      }
    }
    
    if (!testClassId) {
      // 如果沒有選擇測試類別，顯示所有問題
      setFilteredIssues(issues);
    } else {
      // 根據選擇的測試類別過濾問題
      const filtered = issues.filter(issue => 
        issue.test_class === testClassId
      );
      setFilteredIssues(filtered);
    }
  };

  // 當 issues 數據變更時，重新應用過濾（但不保存到 localStorage）
  useEffect(() => {
    console.log('重新應用過濾，selectedTestClass:', selectedTestClass);
    handleTestClassFilter(selectedTestClass, true); // 跳過保存，避免清除用戶選擇
  }, [issues, selectedTestClass]); // 當 issues 或 selectedTestClass 變更時重新過濾

  // 提取自動完成選項
  const extractAutoCompleteOptions = (issues) => {
    const options = {
      testVersions: [...new Set(issues.map(issue => issue.test_version).filter(Boolean))],
      projects: [...new Set(issues.map(issue => issue.project).filter(Boolean))],
      issueTypes: [...new Set(issues.map(issue => issue.issue_type).filter(Boolean))],
      statuses: [...new Set(issues.map(issue => issue.status).filter(Boolean))],
      jiraNumbers: [...new Set(issues.map(issue => issue.jira_number).filter(Boolean))]
    };
    
    // 從本地存儲獲取額外的選項
    try {
      const savedOptions = localStorage.getItem('knowIssueAutoComplete');
      if (savedOptions) {
        const parsed = JSON.parse(savedOptions);
        Object.keys(options).forEach(key => {
          options[key] = [...new Set([...options[key], ...(parsed[key] || [])])];
        });
      }
    } catch (error) {
      console.warn('載入本地自動完成選項失敗:', error);
    }
    
    setAutoCompleteOptions(options);
  };

  // 保存輸入到本地存儲
  const saveToLocalStorage = (field, value) => {
    if (!value || value.trim() === '') return;
    
    try {
      const saved = localStorage.getItem('knowIssueAutoComplete');
      const options = saved ? JSON.parse(saved) : {};
      
      if (!options[field]) options[field] = [];
      if (!options[field].includes(value)) {
        options[field].unshift(value); // 新項目添加到開頭
        if (options[field].length > 20) { // 限制數量
          options[field] = options[field].slice(0, 20);
        }
      }
      
      localStorage.setItem('knowIssueAutoComplete', JSON.stringify(options));
      
      // 更新狀態
      setAutoCompleteOptions(prev => ({
        ...prev,
        [field]: [...new Set([value, ...prev[field]])].slice(0, 20)
      }));
    } catch (error) {
      console.warn('保存自動完成選項失敗:', error);
    }
  };

  // 載入測試類別
  const fetchTestClasses = async () => {
    try {
      const response = await axios.get('/api/test-classes/', {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        }
      });
      
      const classesData = response.data.results || [];
      const activeClasses = classesData.filter(cls => cls.is_active);
      console.log('Loaded test classes:', activeClasses.map(c => ({ id: c.id, name: c.name })));
      setTestClasses(activeClasses);
      
    } catch (error) {
      console.error('載入測試類別失敗:', error);
      
      // 根據錯誤類型顯示不同提示
      if (error.response?.status === 403) {
        console.warn('權限不足：無法載入測試類別列表，請聯繫管理員');
        // 可以在這裡設置一個默認的測試類別或顯示提示
      } else if (error.response?.status === 401) {
        console.warn('未認證：請重新登入');
      } else {
        console.warn('網路錯誤：無法連接到伺服器');
      }
      
      // 設置空的測試類別列表，避免程式崩潰
      setTestClasses([]);
    }
  };

  // 專門處理測試類別選擇恢復的 useEffect
  useEffect(() => {
    if (testClasses.length > 0 && selectedTestClass === null) {
      console.log('Attempting to restore test class selection...');
      try {
        const savedTestClass = localStorage.getItem('selectedTestClass');
        console.log('Saved test class ID:', savedTestClass);
        
        if (savedTestClass) {
          const savedId = parseInt(savedTestClass);
          const validClass = testClasses.find(cls => cls.id === savedId);
          console.log('Found valid class:', validClass);
          
          if (validClass) {
            console.log('恢復測試類別選擇:', validClass.name, validClass.id);
            // 使用 setTimeout 確保狀態更新不會被其他地方覆蓋
            setTimeout(() => {
              setSelectedTestClass(savedId);
            }, 0);
            return;
          } else {
            console.warn('保存的測試類別ID無效:', savedId);
          }
        }
        
        // 如果沒有保存的選擇或選擇無效，則選擇第一個
        console.log('設置默認測試類別:', testClasses[0].name, testClasses[0].id);
        setTimeout(() => {
          setSelectedTestClass(testClasses[0].id);
          localStorage.setItem('selectedTestClass', testClasses[0].id.toString());
        }, 0);
      } catch (error) {
        console.warn('恢復測試類別選擇失敗:', error);
        setTimeout(() => {
          setSelectedTestClass(testClasses[0].id);
          localStorage.setItem('selectedTestClass', testClasses[0].id.toString());
        }, 0);
      }
    }
  }, [testClasses]); // 只依賴 testClasses，避免 selectedTestClass 的競爭條件

  // 調試用的 useEffect - 監控 selectedTestClass 變化
  useEffect(() => {
    console.log('selectedTestClass 狀態變化:', selectedTestClass);
    if (testClasses.length > 0 && selectedTestClass !== null) {
      const selectedClass = testClasses.find(cls => cls.id === selectedTestClass);
      console.log('當前選中的測試類別:', selectedClass?.name);
    }
  }, [selectedTestClass, testClasses]);

  // 載入資料
  const fetchIssues = async () => {
    try {
      setLoading(true);
      console.log('Fetching issues, authenticated:', isAuthenticated, 'user:', user);
      
      // 確保用戶已認證
      if (!isAuthenticated) {
        message.error('請先登入');
        return;
      }
      
      if (!user) {
        message.error('用戶資訊載入失敗');
        return;
      }
      
      const response = await axios.get('/api/know-issues/', {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        }
      });
      
      console.log('API Response:', response.data);
      const issuesData = response.data.results || [];
      setIssues(issuesData);
      setFilteredIssues(issuesData); // 初始化過濾數據
      extractAutoCompleteOptions(issuesData);
    } catch (error) {
      console.error('載入 know issues 失敗:', error);
      console.error('Error response:', error.response);
      console.error('Error status:', error.response?.status);
      console.error('Error data:', error.response?.data);
      
      if (error.response?.status === 401) {
        message.error('認證已過期，請重新登入');
      } else if (error.response?.status === 403) {
        message.error('權限不足，請檢查您的帳戶狀態');
      } else {
        message.error('載入資料失敗: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('KnowIssuePage mounted, isAuthenticated:', isAuthenticated, 'user:', user, 'initialized:', initialized);
    console.log('Current selectedTestClass:', selectedTestClass);
    console.log('localStorage selectedTestClass:', localStorage.getItem('selectedTestClass'));
    
    // 只有在認證狀態初始化完成且用戶已認證時才載入資料
    if (initialized && isAuthenticated && user) {
      fetchIssues();
      fetchTestClasses();
    } else if (initialized && !isAuthenticated) {
      console.log('User not authenticated');
      message.warning('請先登入以查看知識庫');
    }
  }, [isAuthenticated, user, initialized]); // 依賴認證狀態和初始化狀態

  // 表格欄位定義
  const columns = [
    {
      title: '預覽',
      key: 'preview',
      width: 80,
      fixed: 'left',
      render: (_, record) => (
        <Button 
          icon={<DatabaseOutlined />}
          size="small"
          type="text"
          onClick={() => handlePreview(record)}
          title="查看詳細資料"
          style={{ color: '#1890ff' }}
        />
      ),
    },
    {
      title: 'Issue ID',
      dataIndex: 'issue_id',
      key: 'issue_id',
      width: 280,
      fixed: 'left',
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <div style={{ maxWidth: 260 }}>
          <Tag 
            color="blue" 
            title={text} 
            style={{ 
              cursor: 'help',
              maxWidth: '100%',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              display: 'inline-block'
            }}
          >
            {text}
          </Tag>
        </div>
      ),
      sorter: (a, b) => a.issue_id.localeCompare(b.issue_id),
    },
    {
      title: 'Project',
      dataIndex: 'project',
      key: 'project',
      width: 150,
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <div title={text} style={{ cursor: 'help' }}>
          {text}
        </div>
      ),
    },
    {
      title: '測試版本',
      dataIndex: 'test_version',
      key: 'test_version',
      width: 80,
      render: (text) => (
        <div title={text} style={{ cursor: 'help' }}>
          {text}
        </div>
      ),
    },
    {
      title: 'JIRA 號碼',
      dataIndex: 'jira_number',
      key: 'jira_number',
      width: 130,
      render: (text) => text ? (
        <Tag color="orange" title={text} style={{ cursor: 'help' }}>
          {text}
        </Tag>
      ) : '-',
    },
    {
      title: 'Issue Type',
      dataIndex: 'issue_type',
      key: 'issue_type',
      width: 100,
      render: (text) => {
        const colors = {
          'bug': 'red',
          'feature': 'green',
          'improvement': 'blue',
          'task': 'purple',
          'support': 'cyan',
          'other': 'default'
        };
        return (
          <Tag 
            color={colors[text.toLowerCase()] || 'default'} 
            title={text}
            style={{ cursor: 'help' }}
          >
            {text}
          </Tag>
        );
      },
    },
    {
      title: 'Script',
      dataIndex: 'script',
      key: 'script',
      width: 350,
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <div 
          style={{ maxWidth: 350, cursor: text ? 'help' : 'default' }} 
          title={text || '無 Script 內容'}
        >
          {text || '-'}
        </div>
      ),
    },
    {
      title: '圖片',
      key: 'images',
      width: 100,
      render: (_, record) => {
        const imageCount = record.image_count || 0;
        return (
          <div style={{ textAlign: 'center' }}>
            {imageCount > 0 ? (
              <Tag 
                color="green" 
                icon={<PictureOutlined />}
                style={{ cursor: 'pointer' }}
                onClick={() => handlePreview(record)}
                title="點擊查看圖片詳情"
              >
                {imageCount}
              </Tag>
            ) : (
              <Tag color="default">0</Tag>
            )}
          </div>
        );
      },
    },
    {
      title: '錯誤訊息',
      dataIndex: 'error_message',
      key: 'error_message',
      width: 400,
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <div 
          style={{ maxWidth: 400, cursor: 'help' }} 
          title={text}
        >
          {text}
        </div>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Button 
          icon={<EditOutlined />} 
          size="small" 
          onClick={() => handleEdit(record)}
          title="編輯"
        />
      ),
    },
  ];

  // 預覽處理
  const handlePreview = (issue) => {
    setPreviewIssue(issue);
    setPreviewModalVisible(true);
  };

  // 編輯處理
  const handleEdit = (issue) => {
    if (!selectedTestClass) {
      message.warning('請先選擇測試類別過濾條件');
      return;
    }
    
    setEditingIssue(issue);
    
    // 使用過濾器選中的測試類別，而不是原問題的測試類別
    const formValues = { ...issue, test_class: selectedTestClass };
    form.setFieldsValue(formValues);
    
    const selectedClass = testClasses.find(cls => cls.id === selectedTestClass);
    setSelectedFormTestClass(selectedClass);
    
    // 設置現有圖片
    const existingImages = convertExistingImagesToFileList(issue);
    setImageFileList(existingImages);
    
    setModalVisible(true);
  };

  // 刪除處理
  const handleDelete = async (id) => {
    Modal.confirm({
      title: '確認刪除',
      content: '確定要刪除這個問題記錄嗎？',
      onOk: async () => {
        try {
          await axios.delete(`/api/know-issues/${id}/`, {
            withCredentials: true
          });
          message.success('刪除成功');
          fetchIssues();
        } catch (error) {
          message.error('刪除失敗');
        }
      },
    });
  };

  // 新增/編輯提交
  const handleSubmit = async (values) => {
    try {
      // 創建 FormData 以支援圖片上傳
      const formData = new FormData();
      
      // 添加文字欄位
      Object.keys(values).forEach(key => {
        if (values[key] !== null && values[key] !== undefined) {
          formData.append(key, values[key]);
        }
      });
      
      // 處理圖片上傳
      const newImages = imageFileList.filter(file => !file.isExisting);
      newImages.forEach((file, index) => {
        if (file.originFileObj) {
          formData.append(`image${index + 1}`, file.originFileObj);
        }
      });
      
      const config = {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      };
      
      if (editingIssue) {
        await axios.put(`/api/know-issues/${editingIssue.id}/`, formData, config);
        message.success('更新成功');
      } else {
        await axios.post('/api/know-issues/', formData, config);
        message.success('新增成功');
      }
      
      // 保存新的輸入項目到本地存儲
      if (values.test_version) saveToLocalStorage('testVersions', values.test_version);
      if (values.project) saveToLocalStorage('projects', values.project);
      if (values.issue_type) saveToLocalStorage('issueTypes', values.issue_type);
      if (values.status) saveToLocalStorage('statuses', values.status);
      if (values.jira_number) saveToLocalStorage('jiraNumbers', values.jira_number);
      
      setModalVisible(false);
      setSelectedFormTestClass(null);
      setImageFileList([]);
      form.resetFields();
      setEditingIssue(null);
      fetchIssues();
    } catch (error) {
      message.error('操作失敗: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 如果還未初始化，顯示載入狀態
  if (!initialized) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Title level={3}>載入中...</Title>
            <p>正在檢查認證狀態，請稍候</p>
          </div>
        </Card>
      </div>
    );
  }

  // 如果未認證，顯示提示
  if (!isAuthenticated) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Title level={3}>需要登入</Title>
            <p>請登入後才能查看 Know Issue 資料</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        marginBottom: '16px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}>
        <Title level={2} style={{ margin: 0 }}>
          <DatabaseOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          Know Issue 管理
        </Title>
        
        {/* 測試類別過濾器 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '16px', color: '#666', fontWeight: '500' }}>測試類別：</span>
          <Select
            key={`test-class-select-${testClasses.length}-${selectedTestClass}-${Date.now()}`} // 加入時間戳強制重新渲染
            placeholder={
              testClasses.length === 0 
                ? "無可用測試類別" 
                : "選擇測試類別"
            }
            allowClear
            style={{ minWidth: 280, fontSize: '16px' }}
            value={selectedTestClass}
            onChange={(value) => {
              console.log('Select onChange triggered with value:', value);
              handleTestClassFilter(value);
            }}
            showSearch
            size="large"
            disabled={testClasses.length === 0}
            notFoundContent={
              testClasses.length === 0 
                ? "無測試類別數據，請聯繫管理員" 
                : "無匹配結果"
            }
            filterOption={(input, option) =>
              (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
            }
          >
            {testClasses.map(testClass => (
              <Option key={testClass.id} value={testClass.id} style={{ fontSize: '16px' }}>
                {testClass.name}
              </Option>
            ))}
          </Select>
          
          {testClasses.length === 0 && (
            <span style={{ 
              fontSize: '12px', 
              color: '#ff4d4f', 
              fontStyle: 'italic',
              marginLeft: '8px'
            }}>
              ⚠️ 無法載入測試類別
            </span>
          )}
        </div>
        
        <Space>
          <Button 
            icon={<ReloadOutlined />}
            onClick={fetchIssues}
            loading={loading}
          >
            重新載入
          </Button>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            disabled={testClasses.length === 0}
            title={
              testClasses.length === 0 
                ? "無可用測試類別，無法新增問題" 
                : "新增問題"
            }
            onClick={() => {
              if (testClasses.length === 0) {
                message.error('無可用測試類別，請聯繫管理員新增測試類別');
                return;
              }
              
              if (!selectedTestClass) {
                message.warning('請先選擇測試類別過濾條件');
                return;
              }
              
              setEditingIssue(null);
              setImageFileList([]);
              form.resetFields();
              
              // 使用過濾器選中的測試類別
              const selectedClass = testClasses.find(cls => cls.id === selectedTestClass);
              setSelectedFormTestClass(selectedClass);
              form.setFieldsValue({ test_class: selectedTestClass });
              
              setModalVisible(true);
            }}
          >
            新增問題
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={filteredIssues}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
          }}
          bordered
        />
      </Card>

      {/* 新增/編輯 Modal */}
      <Modal
        title={editingIssue ? '編輯問題' : '新增問題'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setSelectedFormTestClass(null);
          setImageFileList([]);
          form.resetFields();
          setEditingIssue(null);
        }}
        onOk={() => form.submit()}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          {/* 測試類別信息顯示（使用過濾器選中的值） */}
          <Form.Item
            name="test_class"
            label="測試類別"
            style={{ display: 'none' }}
          >
            <Input />
          </Form.Item>
          
          {selectedFormTestClass && (
            <div style={{ 
              marginBottom: '16px',
              padding: '12px 16px', 
              backgroundColor: '#e6f7ff', 
              border: '1px solid #91d5ff',
              borderRadius: '8px',
              fontSize: '14px',
              color: '#0050b3'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <strong>📂 測試類別：</strong> 
                <Tag color="blue">{selectedFormTestClass.name}</Tag>
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                <strong>🏷️ Issue ID 格式：</strong> {selectedFormTestClass.name.replace(' ', '_')}-[序號]
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                💡 使用頁面頂部過濾器選中的測試類別
              </div>
            </div>
          )}
          
          <Form.Item
            name="test_version"
            label="測試版本"
            rules={[{ required: true, message: '請輸入測試版本' }]}
          >
            <AutoComplete
              placeholder="例如: v1.0.0"
              options={autoCompleteOptions.testVersions.map(version => ({ value: version }))}
              filterOption={(inputValue, option) =>
                option.value.toLowerCase().includes(inputValue.toLowerCase())
              }
            />
          </Form.Item>
          
          <Form.Item
            name="jira_number"
            label="JIRA 號碼"
          >
            <AutoComplete
              placeholder="例如: PROJ-123"
              options={autoCompleteOptions.jiraNumbers.map(number => ({ value: number }))}
              filterOption={(inputValue, option) =>
                option.value.toLowerCase().includes(inputValue.toLowerCase())
              }
            />
          </Form.Item>
          
          <Form.Item
            name="project"
            label="Project"
            rules={[{ required: true, message: '請輸入專案名稱' }]}
          >
            <AutoComplete
              placeholder="例如: AI Platform Web"
              options={autoCompleteOptions.projects.map(project => ({ value: project }))}
              filterOption={(inputValue, option) =>
                option.value.toLowerCase().includes(inputValue.toLowerCase())
              }
            />
          </Form.Item>
          
          <Form.Item
            name="issue_type"
            label="Issue Type"
            rules={[{ required: true, message: '請輸入問題類型' }]}
          >
            <AutoComplete
              placeholder="例如: Bug, Feature Request, Improvement, Task"
              options={autoCompleteOptions.issueTypes.map(type => ({ value: type }))}
              filterOption={(inputValue, option) =>
                option.value.toLowerCase().includes(inputValue.toLowerCase())
              }
            />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="修復狀態"
            rules={[{ required: true, message: '請輸入狀態' }]}
          >
            <AutoComplete
              placeholder="例如: 開放中, 處理中, 已解決, 已關閉"
              options={autoCompleteOptions.statuses.map(status => ({ value: status }))}
              filterOption={(inputValue, option) =>
                option.value.toLowerCase().includes(inputValue.toLowerCase())
              }
            />
          </Form.Item>
          
          <Form.Item
            name="error_message"
            label="錯誤訊息"
            rules={[{ required: true, message: '請輸入錯誤訊息' }]}
          >
            <Input.TextArea rows={6} placeholder="請描述具體的錯誤訊息..." />
          </Form.Item>
          
          <Form.Item
            name="script"
            label="Script"
          >
            <Input.TextArea rows={6} placeholder="相關的腳本或代碼..." />
          </Form.Item>
          
          <Form.Item
            name="supplement"
            label="補充"
          >
            <Input.TextArea rows={6} placeholder="額外的補充說明或解決方案..." />
          </Form.Item>
          
          {/* 圖片上傳欄位 */}
          <Form.Item
            label="相關圖片"
            extra="最多上傳 5 張圖片，每張圖片大小不超過 5MB"
          >
            <Upload
              listType="picture-card"
              fileList={imageFileList}
              onPreview={handleImagePreview}
              onChange={handleImageUpload}
              beforeUpload={beforeUpload}
              multiple
              accept="image/*"
            >
              {imageFileList.length < 5 && (
                <div>
                  <PlusOutlined />
                  <div style={{ marginTop: 8 }}>上傳圖片</div>
                </div>
              )}
            </Upload>
          </Form.Item>
        </Form>
      </Modal>

      {/* 圖片預覽 Modal */}
      <Modal
        open={imageModalVisible}
        title="圖片預覽"
        footer={null}
        onCancel={() => setImageModalVisible(false)}
        width={800}
        centered
      >
        <img
          alt="preview"
          style={{ width: '100%' }}
          src={currentImageSrc}
        />
      </Modal>

      {/* 預覽 Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DatabaseOutlined style={{ color: '#1890ff' }} />
            <span>資料預覽</span>
            {previewIssue && (
              <Tag color="blue" style={{ marginLeft: '8px' }}>
                {previewIssue.issue_id}
              </Tag>
            )}
          </div>
        }
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false);
          setPreviewIssue(null);
        }}
        footer={[
          <Button key="close" onClick={() => {
            setPreviewModalVisible(false);
            setPreviewIssue(null);
          }}>
            關閉
          </Button>,
          <Button 
            key="edit" 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => {
              setPreviewModalVisible(false);
              handleEdit(previewIssue);
            }}
          >
            編輯
          </Button>
        ]}
        width={900}
      >
        {previewIssue && (
          <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            {/* 基本信息 */}
            <div style={{ 
              marginBottom: '20px',
              padding: '16px',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #e9ecef'
            }}>
              <Title level={4} style={{ margin: '0 0 12px 0', color: '#1890ff' }}>
                📝 基本信息
              </Title>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <strong>📂 Issue ID：</strong>
                  <Tag color="blue" style={{ marginLeft: '8px' }}>{previewIssue.issue_id}</Tag>
                </div>
                <div>
                  <strong>📁 Project：</strong>
                  <span style={{ marginLeft: '8px' }}>{previewIssue.project}</span>
                </div>
                <div>
                  <strong>📊 測試版本：</strong>
                  <span style={{ marginLeft: '8px' }}>{previewIssue.test_version}</span>
                </div>
                <div>
                  <strong>🏷️ 測試類別：</strong>
                  <Tag color="green" style={{ marginLeft: '8px' }}>
                    {previewIssue.test_class_name || '-'}
                  </Tag>
                </div>
                <div>
                  <strong>🔗 JIRA 號碼：</strong>
                  {previewIssue.jira_number ? (
                    <Tag color="orange" style={{ marginLeft: '8px' }}>{previewIssue.jira_number}</Tag>
                  ) : (
                    <span style={{ marginLeft: '8px', color: '#999' }}>-</span>
                  )}
                </div>
                <div>
                  <strong>🔄 問題類型：</strong>
                  <Tag 
                    color={
                      {
                        'bug': 'red',
                        'feature': 'green',
                        'improvement': 'blue',
                        'task': 'purple',
                        'support': 'cyan',
                        'other': 'default'
                      }[previewIssue.issue_type?.toLowerCase()] || 'default'
                    }
                    style={{ marginLeft: '8px' }}
                  >
                    {previewIssue.issue_type}
                  </Tag>
                </div>
                <div>
                  <strong>📊 修復狀態：</strong>
                  <span style={{ marginLeft: '8px' }}>{previewIssue.status}</span>
                </div>
                <div>
                  <strong>📅 建立時間：</strong>
                  <span style={{ marginLeft: '8px' }}>
                    {previewIssue.created_at ? new Date(previewIssue.created_at).toLocaleString('zh-TW') : '-'}
                  </span>
                </div>
              </div>
            </div>

            {/* 錯誤訊息 */}
            <div style={{ 
              marginBottom: '20px',
              padding: '16px',
              backgroundColor: '#fff2f0',
              borderRadius: '8px',
              border: '1px solid #ffccc7'
            }}>
              <Title level={4} style={{ margin: '0 0 12px 0', color: '#cf1322' }}>
                ⚠️ 錯誤訊息
              </Title>
              <div style={{ 
                backgroundColor: 'white',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #f5f5f5',
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
                fontSize: '14px',
                lineHeight: '1.6'
              }}>
                {previewIssue.error_message || '無錯誤訊息'}
              </div>
            </div>

            {/* Script */}
            {previewIssue.script && (
              <div style={{ 
                marginBottom: '20px',
                padding: '16px',
                backgroundColor: '#f6ffed',
                borderRadius: '8px',
                border: '1px solid #b7eb8f'
              }}>
                <Title level={4} style={{ margin: '0 0 12px 0', color: '#52c41a' }}>
                  📄 Script
                </Title>
                <div style={{ 
                  backgroundColor: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '6px',
                  border: '1px solid #d9d9d9',
                  fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                  fontSize: '13px',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                  overflow: 'auto'
                }}>
                  {previewIssue.script}
                </div>
              </div>
            )}

            {/* 補充說明 */}
            {previewIssue.supplement && (
              <div style={{ 
                marginBottom: '20px',
                padding: '16px',
                backgroundColor: '#e6f7ff',
                borderRadius: '8px',
                border: '1px solid #91d5ff'
              }}>
                <Title level={4} style={{ margin: '0 0 12px 0', color: '#1890ff' }}>
                  📝 補充說明
                </Title>
                <div style={{ 
                  backgroundColor: 'white',
                  padding: '12px',
                  borderRadius: '6px',
                  border: '1px solid #f5f5f5',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                  fontSize: '14px',
                  lineHeight: '1.6'
                }}>
                  {previewIssue.supplement}
                </div>
              </div>
            )}

            {/* 圖片附件 */}
            {previewIssue.image_urls && previewIssue.image_urls.length > 0 && (
              <div style={{ 
                marginBottom: '20px',
                padding: '16px',
                backgroundColor: '#f9f0ff',
                borderRadius: '8px',
                border: '1px solid #d3adf7'
              }}>
                <Title level={4} style={{ margin: '0 0 12px 0', color: '#722ed1' }}>
                  🖼️ 相關圖片 ({previewIssue.image_count || previewIssue.image_urls.length})
                </Title>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                  gap: '12px'
                }}>
                  {previewIssue.image_urls.map((imageUrl, index) => (
                    imageUrl && (
                      <div key={index} style={{ 
                        border: '1px solid #e9ecef',
                        borderRadius: '8px',
                        overflow: 'hidden',
                        backgroundColor: 'white'
                      }}>
                        <Image
                          src={imageUrl}
                          alt={`問題圖片 ${index + 1}`}
                          style={{ 
                            width: '100%',
                            height: '150px',
                            objectFit: 'cover'
                          }}
                          preview={{
                            mask: (
                              <div style={{ 
                                display: 'flex', 
                                flexDirection: 'column', 
                                alignItems: 'center', 
                                gap: '4px',
                                color: 'white'
                              }}>
                                <EyeOutlined style={{ fontSize: '20px' }} />
                                <span style={{ fontSize: '12px' }}>預覽</span>
                              </div>
                            )
                          }}
                        />
                        <div style={{ 
                          padding: '8px',
                          textAlign: 'center',
                          fontSize: '12px',
                          color: '#666',
                          backgroundColor: '#f8f9fa'
                        }}>
                          圖片 {index + 1}
                        </div>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}

            {/* 系統信息 */}
            <div style={{ 
              padding: '16px',
              backgroundColor: '#fafafa',
              borderRadius: '8px',
              border: '1px solid #d9d9d9'
            }}>
              <Title level={4} style={{ margin: '0 0 12px 0', color: '#666' }}>
                📊 系統信息
              </Title>
              <div style={{ fontSize: '13px', color: '#666', lineHeight: '1.8' }}>
                <div style={{ marginBottom: '8px' }}>
                  <strong>🆔 記錄ID：</strong> 
                  <span style={{ marginLeft: '8px', fontFamily: 'monospace' }}>{previewIssue.id}</span>
                </div>
                {previewIssue.updated_by_name && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>✏️ 修改者：</strong> 
                    <Tag color="orange" size="small" style={{ marginLeft: '8px' }}>
                      {previewIssue.updated_by_name}
                    </Tag>
                  </div>
                )}
                {previewIssue.created_at && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>📅 建立時間：</strong> 
                    <span style={{ marginLeft: '8px' }}>
                      {new Date(previewIssue.created_at).toLocaleString('zh-TW')}
                    </span>
                  </div>
                )}
                {previewIssue.updated_at && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>🔄 更新時間：</strong> 
                    <span style={{ marginLeft: '8px' }}>
                      {new Date(previewIssue.updated_at).toLocaleString('zh-TW')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default KnowIssuePage;