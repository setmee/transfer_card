// API接口配置
const API_BASE_URL = 'http://localhost:5000/api';

// 获取认证token
function getAuthToken() {
    return localStorage.getItem('authToken');
}

// 设置认证token
function setAuthToken(token) {
    localStorage.setItem('authToken', token);
}

// 清除认证token
function clearAuthToken() {
    localStorage.removeItem('authToken');
}

// 创建axios实例
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000
});

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
    config => {
        const token = getAuthToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
    response => {
        return response.data;
    },
    error => {
        if (error.response) {
            const url = error.config.url;
            const isLoginRequest = url && url.includes('/auth/login');
            
            switch (error.response.status) {
                case 401:
                    if (isLoginRequest) {
                        // 登录请求的401错误，显示具体错误信息
                        const errorMessage = error.response.data?.message || '用户名或密码错误';
                        console.error(errorMessage);
                        break;
                    } else {
                        // 其他401错误，清除token并跳转到登录页
                        clearAuthToken();
                        window.location.href = '/index.html';
                        break;
                    }
                case 403:
                    // 权限不足
                    console.error('权限不足');
                    break;
                case 404:
                    // 资源不存在
                    console.error('请求的资源不存在');
                    break;
                case 500:
                    // 服务器错误
                    console.error('服务器内部错误');
                    break;
                default:
                    // 其他错误 - 显示服务器返回的具体错误信息
                    const errorMessage = error.response.data?.message || '请求失败';
                    console.error(errorMessage);
            }
        } else if (error.request) {
            console.error('网络连接失败');
        } else {
            console.error('请求配置错误');
        }
        return Promise.reject(error);
    }
);

// 认证相关API
const authAPI = {
    // 登录
    login: (username, password, loginType = 'user', departmentId = null) => {
        const loginData = { username, password, login_type: loginType };
        if (loginType === 'user' && departmentId) {
            loginData.department_id = departmentId;
        }
        return api.post('/auth/login', loginData);
    },
    
    // 退出登录
    logout: () => {
        return api.post('/auth/logout');
    },
    
    // 刷新token
    refreshToken: () => {
        return api.post('/auth/refresh');
    }
};

// 用户管理API
const userAPI = {
    // 获取用户列表
    getUsers: () => {
        return api.get('/users');
    },
    
    // 获取单个用户
    getUser: (id) => {
        return api.get(`/users/${id}`);
    },
    
    // 创建用户
    createUser: (userData) => {
        return api.post('/users', userData);
    },
    
    // 更新用户
    updateUser: (id, userData) => {
        return api.put(`/users/${id}`, userData);
    },
    
    // 删除用户
    deleteUser: (id) => {
        return api.delete(`/users/${id}`);
    },
    
    // 获取部门列表
    getDepartments: () => {
        return api.get('/departments');
    },
    
    // 创建部门
    createDepartment: (departmentData) => {
        return api.post('/departments', departmentData);
    },
    
    // 更新部门
    updateDepartment: (id, departmentData) => {
        return api.put(`/departments/${id}`, departmentData);
    },
    
    // 删除部门
    deleteDepartment: (id) => {
        return api.delete(`/departments/${id}`);
    },
    
    // 获取用户操作历史
    getUserHistory: (userId) => {
        return api.get(`/users/${userId}/history`);
    },
    
    // 获取当前用户信息
    getCurrentUser: () => {
        return api.get('/auth/profile');
    }
};

// 字段管理API
const fieldAPI = {
    // 获取字段列表
    getFields: () => {
        return api.get('/fields');
    },
    
    // 获取单个字段
    getField: (id) => {
        return api.get(`/fields/${id}`);
    },
    
    // 创建字段
    createField: (fieldData) => {
        return api.post('/fields', fieldData);
    },
    
    // 更新字段
    updateField: (id, fieldData) => {
        return api.put(`/fields/${id}`, fieldData);
    },
    
    // 删除字段
    deleteField: (id) => {
        return api.delete(`/fields/${id}`);
    },
    
    // 获取字段权限
    getFieldPermissions: (departmentId) => {
        return api.get('/fields/permissions', {
            params: { department_id: departmentId }
        });
    },
    
    // 更新字段权限
    updateFieldPermissions: (permissions) => {
        return api.post('/fields/permissions', permissions);
    },
    
    // 获取可用的预留字段
    getAvailablePlaceholderFields: () => {
        return api.get('/fields/available-placeholders');
    }
};

// 流转卡管理API
const cardAPI = {
    // 获取流转卡列表
    getCards: (params = {}) => {
        return api.get('/cards', { params });
    },
    
    // 获取单个流转卡
    getCard: (id) => {
        return api.get(`/cards/${id}`);
    },
    
    // 创建流转卡
    createCard: (cardData) => {
        return api.post('/cards', cardData);
    },
    
    // 更新流转卡
    updateCard: (id, cardData) => {
        return api.put(`/cards/${id}`, cardData);
    },
    
    // 删除流转卡
    deleteCard: (id) => {
        return api.delete(`/cards/${id}`);
    },
    
    // 更新流转卡数据
    updateCardData: (id, fieldData) => {
        return api.put(`/cards/${id}/data`, fieldData);
    },
    
    // 获取流转卡操作日志
    getCardLogs: (id) => {
        return api.get(`/cards/${id}/logs`);
    },
    
    // 获取流转卡数据（表格格式）
    getCardData: (id) => {
        return api.get(`/cards/${id}/data`);
    },
    
    // 批量保存流转卡数据
    saveCardData: (id, rowData) => {
        return api.post(`/cards/${id}/data`, { row_data: rowData });
    }
};

// 模板管理API
const templateAPI = {
    // 获取模板列表
    getTemplates: (params = {}) => {
        return api.get('/templates', { params });
    },
    
    // 获取单个模板
    getTemplate: (id) => {
        return api.get(`/templates/${id}`);
    },
    
    // 创建模板
    createTemplate: (templateData) => {
        return api.post('/templates', templateData);
    },
    
    // 更新模板
    updateTemplate: (id, templateData) => {
        return api.put(`/templates/${id}`, templateData);
    },
    
    // 删除模板
    deleteTemplate: (id) => {
        return api.delete(`/templates/${id}`);
    },
    
    // 获取模板字段列表
    getTemplateFields: (templateId) => {
        return api.get(`/templates/${templateId}/fields`);
    },
    
    // 创建模板字段
    createTemplateField: (fieldData) => {
        return api.post('/template-fields', fieldData);
    },
    
    // 更新模板字段
    updateTemplateField: (id, fieldData) => {
        return api.put(`/template-fields/${id}`, fieldData);
    },
    
    // 删除模板字段
    deleteTemplateField: (id) => {
        return api.delete(`/template-fields/${id}`);
    },
    
    // 基于模板创建流转卡
    createTemplateCard: (cardData) => {
        return api.post('/template-cards', cardData);
    },
    
    // 批量更新模板字段
    updateTemplateFields: (templateId, fieldsData) => {
        return api.put(`/templates/${templateId}/fields`, fieldsData);
    },
    
    // 获取基于模板的流转卡列表
    getTemplateCards: (params = {}) => {
        return api.get('/template-cards', { params });
    },
    
    // 获取单个基于模板的流转卡
    getTemplateCard: (id) => {
        return api.get(`/template-cards/${id}`);
    },
    
    // 更新基于模板的流转卡
    updateTemplateCard: (id, cardData) => {
        return api.put(`/template-cards/${id}`, cardData);
    },
    
    // 删除基于模板的流转卡
    deleteTemplateCard: (id) => {
        return api.delete(`/template-cards/${id}`);
    },
    
    // 发布流转卡
    publishTemplateCard: (id) => {
        return api.post(`/template-cards/${id}/publish`);
    },
    
    // 创建表格格式的模板流转卡
    createTemplateCardWithTableData: (cardData) => {
        return api.post('/template-cards/table-format', cardData);
    }
};

// 工具函数
const utils = {
    // 格式化日期时间
    formatDateTime: (dateTimeStr) => {
        if (!dateTimeStr) return '';
        const date = new Date(dateTimeStr);
        return date.toLocaleString('zh-CN');
    },
    
    // 格式化日期
    formatDate: (dateStr) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN');
    },
    
    // 获取状态文本
    getStatusText: (status) => {
        const statusMap = {
            'draft': '草稿',
            'in_progress': '进行中',
            'completed': '已完成',
            'cancelled': '已取消'
        };
        return statusMap[status] || status;
    },
    
    // 获取状态类型
    getStatusType: (status) => {
        const typeMap = {
            'draft': 'warning',
            'in_progress': 'primary',
            'completed': 'success',
            'cancelled': 'danger'
        };
        return typeMap[status] || 'info';
    },
    
    // 获取字段类型显示文本
    getFieldTypeText: (fieldType) => {
        const typeMap = {
            'text': '文本',
            'number': '数字',
            'date': '日期',
            'select': '选择',
            'boolean': '布尔'
        };
        return typeMap[fieldType] || fieldType;
    },
    
    // 深拷贝对象
    deepClone: (obj) => {
        return JSON.parse(JSON.stringify(obj));
    },
    
    // 生成随机ID
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
};

// 导出API和工具函数
window.TransferCardAPI = {
    auth: authAPI,
    user: userAPI,
    field: fieldAPI,
    card: cardAPI,
    template: templateAPI,
    utils: utils,
    setAuthToken,
    clearAuthToken,
    getAuthToken
};
