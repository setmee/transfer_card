// Vue应用主文件
new Vue({
    el: '#app',
    data() {
        return {
            // 登录状态
            isLoggedIn: false,
            currentUser: null,
            
            // 当前激活的菜单
            activeMenu: 'dashboard',
            
            // 登录表单
            loginForm: {
                username: '',
                password: '',
                department_id: null
        },

        // 捕获当前用户编辑的内容
        captureCurrentUserEdits() {
            const currentUserEdits = new Map();
            
            try {
                console.log(' 开始捕获当前用户编辑内容');
                
                // 查找所有可能的输入框
                const inputs = document.querySelectorAll(
                    'input.el-input__inner, ' +
                    'input[type="text"], ' +
                    'textarea, ' +
                    'input:not([type]), ' +
                    '.el-input input'
                );
                
                console.log(` 找到 ${inputs.length} 个输入框元素`);
                
                inputs.forEach((input, index) => {
                    try {
                        console.log(` 检查输入框 ${index}:`, {
                            tagName: input.tagName,
                            type: input.type,
                            className: input.className,
                            value: input.value,
                            placeholder: input.placeholder
                        });
                        
                        // 获取行号
                        let rowNumber = null;
                        
                        // 方法1：通过父级tr元素获取
                        const tr = input.closest('tr');
                        if (tr) {
                            const allRows = Array.from(tr.parentNode.children);
                            rowNumber = allRows.indexOf(tr) + 1;
                            console.log(`📍 通过tr元素获取行号: ${rowNumber}`);
                        }
                        
                        // 方法2：通过data属性获取
                        if (!rowNumber) {
                            rowNumber = input.getAttribute('data-row-number') || 
                                       input.closest('[data-row-number]')?.getAttribute('data-row-number');
                            if (rowNumber) {
                                rowNumber = parseInt(rowNumber);
                                console.log(`📍 通过data属性获取行号: ${rowNumber}`);
                            }
                        }
                        
                        // 方法3：通过行号列获取
                        if (!rowNumber) {
                            const rowNumberCell = tr?.querySelector('td:first-child, .el-table__cell:first-child');
                            if (rowNumberCell) {
                                const rowText = rowNumberCell.textContent.trim();
                                const match = rowText.match(/\d+/);
                                if (match) {
                                    rowNumber = parseInt(match[0]);
                                    console.log(`📍 通过行号列获取行号: ${rowNumber}`);
                                }
                            }
                        }
                        
                        // 获取字段名
                        let fieldName = null;
                        
                        // 方法1：通过data属性获取
                        fieldName = input.getAttribute('data-field-name') || 
                                  input.closest('[data-field-name]')?.getAttribute('data-field-name');
                        
                        // 方法2：通过name属性获取
                        if (!fieldName && input.name) {
                            fieldName = input.name;
                        }
                        
                        // 方法3：通过表头获取
                        if (!fieldName && tr) {
                            const inputIndex = Array.from(tr.querySelectorAll('input, textarea')).indexOf(input);
                            const table = tr.closest('table');
                            if (table && inputIndex >= 0) {
                                const headers = table.querySelectorAll('th');
                                if (headers[inputIndex]) {
                                    fieldName = headers[inputIndex].textContent.trim();
                                    console.log(`📍 通过表头获取字段名: ${fieldName}`);
                                }
                            }
                        }
                        
                        console.log(`📍 输入框 ${index} 解析结果:`, {
                            rowNumber,
                            fieldName,
                            value: input.value
                        });
                        
                        // 如果有值且能识别位置，就记录
                        if (rowNumber && fieldName && input.value.trim() !== '') {
                            if (!currentUserEdits.has(rowNumber)) {
                                currentUserEdits.set(rowNumber, {});
                            }
                            currentUserEdits.get(rowNumber)[fieldName] = input.value;
                            console.log(`  捕获到用户编辑: 行${rowNumber} 字段${fieldName} = "${input.value}"`);
                        } else {
                            console.log(`  跳过输入框 ${index}:`, {
                                hasRowNumber: !!rowNumber,
                                hasFieldName: !!fieldName,
                                hasValue: input.value.trim() !== '',
                                value: input.value
                            });
                        }
                        
                    } catch (error) {
                        console.error(` 处理输入框 ${index} 失败:`, error);
                    }
                });
                
                console.log('🎯 捕获完成，结果:', currentUserEdits);
                console.log('🎯 捕获的编辑数量:', currentUserEdits.size);
                
            } catch (error) {
                console.error(' 捕获当前用户编辑失败:', error);
            }
            
            return currentUserEdits;
        },

        // 智能合并服务器数据和当前用户编辑
        mergeServerAndUserData(serverData, currentUserEdits) {
            try {
                const serverTableData = serverData.table_data || [];
                const mergedData = [];
                
                serverTableData.forEach((serverRow, index) => {
                    const rowNumber = index + 1;
                    const userEdit = currentUserEdits.get(rowNumber);
                    
                    // 创建合并后的行
                    const mergedRow = { ...serverRow };
                    
                    // 如果用户正在编辑这一行，用户编辑内容优先
                    if (userEdit && Object.keys(userEdit).length > 0) {
                        mergedRow.values = { ...serverRow.values, ...userEdit };
                        console.log(`🔒 行${rowNumber}: 用户编辑优先，合并字段:`, Object.keys(userEdit));
                    }
                    
                    mergedData.push(mergedRow);
                });
                
                return mergedData;
                
            } catch (error) {
                console.error(' 合并服务器数据和用户编辑失败:', error);
                return serverData.table_data || [];
            }
        },

        // 恢复用户编辑到输入框
        restoreUserEdits(currentUserEdits) {
            try {
                currentUserEdits.forEach((fields, rowNumber) => {
                    Object.entries(fields).forEach(([fieldName, value]) => {
                        const input = this.findInputForRowAndField(rowNumber, fieldName);
                        if (input && input.value !== value) {
                            input.value = value;
                            
                            // 触发Vue的input事件
                            const event = new Event('input', { bubbles: true });
                            input.dispatchEvent(event);
                            
                            console.log(` 恢复用户编辑: 行${rowNumber} 字段${fieldName} = "${value}"`);
                        }
                    });
                });
                
            } catch (error) {
                console.error(' 恢复用户编辑失败:', error);
            }
        },

        // 检测服务器数据是否有变化
        detectServerChanges(serverData) {
            try {
                if (!this.cardDataEditForm.table_data) {
                    return true; // 如果没有本地数据，认为有变化
                }
                
                const localData = this.cardDataEditForm.table_data;
                const serverTableData = serverData.table_data || [];
                
                // 检查行数是否变化
                if (localData.length !== serverTableData.length) {
                    return true;
                }
                
                // 检查每行是否有变化
                for (let i = 0; i < serverTableData.length; i++) {
                    const localRow = localData[i];
                    const serverRow = serverTableData[i];
                    
                    if (!localRow || !serverRow) {
                        return true;
                    }
                    
                    // 检查字段值是否有变化
                    const localValues = localRow.values || {};
                    const serverValues = serverRow.values || {};
                    
                    const fields = new Set([...Object.keys(localValues), ...Object.keys(serverValues)]);
                    
                    for (const field of fields) {
                        if (localValues[field] !== serverValues[field]) {
                            console.log(` 检测到字段变化: 行${i+1} 字段${field} "${localValues[field]}" -> "${serverValues[field]}"`);
                            return true;
                        }
                    }
                }
                
                return false;
                
            } catch (error) {
                console.error(' 检测服务器数据变化失败:', error);
                return true; // 出错时认为有变化
            }
        },
            
            // 登录类型
            loginType: 'user',
            loginRules: {
                username: [
                    { required: true, message: '请输入用户名', trigger: 'blur' }
                ],
                password: [
                    { required: true, message: '请输入密码', trigger: 'blur' }
                ],
                department_id: [
                    { required: true, message: '请选择部门', trigger: 'change' }
                ]
            },
            departments: [],
            
            // 工作台数据
            dashboardData: {
                pendingCards: 5,
                completedToday: 3,
                weeklyTotal: 12,
                totalCards: 28,
                pendingTrend: 'up',
                pendingChange: 15,
                completedTrend: 'down',
                completedChange: -8,
                weeklyTrend: 'up',
                weeklyChange: 12,
                totalTrend: 'up',
                totalChange: 5
            },
            
            // 静默数据更新（用户无感知）
            updateInterval: 30000, // 30秒更新一次
            realTimeUpdateTimer: null,
            previousData: null,
            recentOperations: [],
            loadingOperations: false,
            operationFilter: '',
            hasMoreOperations: true,
            currentPage: 1,
            
            // 流转卡数据
            cards: [],
            cardDialogVisible: false,
            isEditMode: false,
            cardForm: {
                id: null,
                card_number: '',
                material_code: '',
                material_description: '',
                specification: '',
                material_group: '',
                status: 'draft',
                field_data: {}
            },
            editableFields: [],
            
            // 用户管理数据
            users: [],
            userDialogVisible: false,
            isUserEditMode: false,
            userForm: {
                id: null,
                username: '',
                password: '',
                real_name: '',
                email: '',
                department_id: null,
                role: 'user'
            },
            
            // 部门管理数据
            departmentDialogVisible: false,
            isDepartmentEditMode: false,
            departmentForm: {
                id: null,
                name: '',
                description: ''
            },
            
            // 字段管理数据
            fields: [],
            fieldDialogVisible: false,
            isFieldEditMode: false,
            fieldDepartmentFilter: '',
            fieldTypeFilter: '',
            fieldForm: {
                id: null,
                name: '',
                display_name: '',
                field_type: 'text',
                department_name: '',
                category: '',
                validation_rules: '',
                options: '',
                is_required: false,
                is_hidden: false
            },
            
            // 状态更新防护
            statusUpdating: false,
            fieldTypes: [
                { value: 'text', label: '文本' },
                { value: 'number', label: '数字' },
                { value: 'date', label: '日期' },
                { value: 'select', label: '选择' },
                { value: 'boolean', label: '布尔' }
            ],
            
            // 模板管理数据
            templates: [],
            templateDialogVisible: false,
            isTemplateEditMode: false,
            templateStatusFilter: '',
            templateForm: {
                id: null,
                template_name: '',
                template_description: '',
                is_active: true
            },
            
            // 模板字段管理数据
            currentTemplate: {},
            templateFields: [],
            templateFieldDialogVisible: false,
            isTemplateFieldEditMode: false,
            templateFieldForm: {
                id: null,
                template_id: null,
                field_name: '',
                field_order: 1,
                is_required: false,
                default_value: ''
            },
            
            // 新的字段管理数据
            allFieldsForTemplate: [],
            filteredTemplateFields: [],
            fieldSearchKeyword: '',
            selectAllFields: false,
            isSelectAllIndeterminate: false,
            
            // 基于模板创建流转卡数据
            createCardFromTemplateDialogVisible: false,
            templateCardForm: {
                card_number: '',
                template_id: null,
                title: '',
                description: '',
                row_count: 5,
                responsible_person: '',
                create_date: '',
                status: 'draft',
                field_data: {}
            },
            currentTemplateFields: [],
            
            // 表格格式相关数据
            selectAllTemplateFields: false,
            isSelectAllTemplateFieldsIndeterminate: false,
            previewTableData: [],

            // 部门流转顺序设置数据
            flowSettingsDialogVisible: false,
            flowSettingsTemplate: {},
            templateFlowDepartments: [],
            availableDepartmentsForFlow: [],
            addingDepartmentToFlow: false,
            newDepartmentForFlow: null,
            
            // 流转卡详情和表格显示相关数据
            templateCards: [],
            currentTemplateCard: null,
            currentTemplateCardData: [],
            uniqueDepartments: [],
            cardDataRows: [],
            
            // 新增的流转卡管理相关数据
            loading: false,
            cardSearchKeyword: '',
            cardStatusFilter: '',
            cardTemplateFilter: '',
            cardDetailDialogVisible: false,
            cardDataEditDialogVisible: false,
            currentCardDetail: null,
            cardDataTable: [],
            cardDataTableWithDepartment: [],
            cardDetailFields: [],
            currentEditingCard: null,
            cardDataEditForm: {
                status: '',
                table_data: []
            },
            cardDataEditFields: [],
            
            // 查看模式标志
            isViewMode: false,
            
            // 快速创建流转卡相关
            createCardStep: 0,
            selectedTemplate: null,
            creatingCard: false,
            quickCreateForm: {
                card_number: '',
                title: '',
                description: '',
                responsible_person: '',
                row_count: 5,
                create_date: new Date(),
                status: 'draft'
            },
            quickCreateRules: {
                card_number: [
                    { required: true, message: '请输入流转卡号', trigger: 'blur' }
                ],
                title: [
                    { required: true, message: '请输入流转卡标题', trigger: 'blur' }
                ]
            },
            
            // 简化数据同步相关数据
            dataSyncEnabled: false,
            currentEditingCardId: null,
            lastSyncTime: null,
            syncStatus: 'stopped', // stopped, running, error
            syncFrequency: 2000, // 2秒同步一次
            pendingChanges: {},
            otherUsersData: new Map(), // 存储其他用户的数据变化
            
            
            // 数据同步相关数据
            collaborationToken: null,
            conflictResolution: null,
            mergedData: null,
            lastMergeTime: null,
            syncErrors: [],
            
            // 实时同步相关数据
            realtimeSyncClient: null,
            realtimeSyncStatus: 'disconnected',
            realtimeConnectedUsers: new Map(),
            realtimeChangeQueue: [],
            realtimeSyncTimer: null,
            realtimeSyncFrequency: 3000, // 3秒同步一次
            realtimeLastSyncTime: null,
            realtimeSyncErrors: []
        };
    },
    
    computed: {
        // 是否为管理员
        isAdmin() {
            return this.currentUser && this.currentUser.role === 'admin';
        },
        
        // 是否可以查看流转卡
        canViewCards() {
            return this.currentUser && (this.isAdmin || this.currentUser.department_id);
        },
        
        // 筛选后的字段列表（隐藏预留字段）
        filteredFields() {
            let filtered = this.fields || [];
            
            // 隐藏预留字段
            filtered = filtered.filter(field => !field.is_placeholder);
            
            // 按部门筛选
            if (this.fieldDepartmentFilter) {
                filtered = filtered.filter(field => {
                    if (this.fieldDepartmentFilter === '未分类') {
                        return !field.department_name || field.department_name === '';
                    }
                    return field.department_name === this.fieldDepartmentFilter;
                });
            }
            
            // 按类型筛选
            if (this.fieldTypeFilter) {
                filtered = filtered.filter(field => field.field_type === this.fieldTypeFilter);
            }
            
            return filtered;
        },
        
        // 筛选后的模板列表
        filteredTemplates() {
            let filtered = this.templates || [];
            
            // 按状态筛选
            if (this.templateStatusFilter) {
                if (this.templateStatusFilter === 'true') {
                    filtered = filtered.filter(template => 
                        template.is_active === 1 || template.is_active === true
                    );
                } else if (this.templateStatusFilter === 'false') {
                    filtered = filtered.filter(template => 
                        template.is_active === 0 || template.is_active === false
                    );
                }
            }
            
            return filtered;
        },
        
        // 选中的字段数量
        selectedFieldCount() {
            if (!this.filteredTemplateFields) return 0;
            return this.filteredTemplateFields.filter(field => field.selected).length;
        },
        
        // 字段计数显示格式（业务字段数/总字段数）
        fieldCountDisplay() {
            const businessFields = this.fields ? this.fields.filter(field => !field.is_placeholder).length : 0;
            const totalFields = this.fields ? this.fields.length : 0;
            return `${businessFields}/${totalFields}`;
        },

        // 选中的模板字段数量
        selectedTemplateFieldCount() {
            if (!this.currentTemplateFields) return 0;
            return this.currentTemplateFields.filter(field => field.selected).length;
        },

        // 选中的模板字段（用于预览）
        selectedTemplateFieldsForPreview() {
            if (!this.currentTemplateFields) return [];
            return this.currentTemplateFields.filter(field => field.selected);
        },

        // 筛选后的流转卡列表
        filteredTemplateCards() {
            let filtered = this.templateCards || [];
            
            // 按关键词搜索
            if (this.cardSearchKeyword) {
                const keyword = this.cardSearchKeyword.toLowerCase();
                filtered = filtered.filter(card => 
                    card.card_number.toLowerCase().includes(keyword) ||
                    card.title.toLowerCase().includes(keyword)
                );
            }
            
            // 按状态筛选
            if (this.cardStatusFilter) {
                filtered = filtered.filter(card => card.status === this.cardStatusFilter);
            }
            
            // 按模板筛选
            if (this.cardTemplateFilter) {
                filtered = filtered.filter(card => card.template_name === this.cardTemplateFilter);
            }
            
            return filtered;
        }
    },
    
    created() {
        this.checkLoginStatus();
        this.loadPublicDepartments();
    },

    mounted() {
        // 启动实时数据更新
        this.startRealTimeUpdates();
        
        // 初始化数据同步
        this.$nextTick(() => {
            this.initializeDataSync();
        });
    },

    beforeDestroy() {
        // 清理定时器
        this.stopRealTimeUpdates();
    },

    watch: {
        fieldSearchKeyword() {
            this.updateFilteredTemplateFields();
        },
        
        fieldDepartmentFilter() {
            this.updateFilteredTemplateFields();
        },
        
        fieldTypeFilter() {
            this.updateFilteredTemplateFields();
        },
        
    },
    
    methods: {
        // 检查登录状态
        async checkLoginStatus() {
            const token = TransferCardAPI.getAuthToken();
            if (token) {
                try {
                    const response = await TransferCardAPI.auth.refreshToken();
                    if (response.success) {
                        TransferCardAPI.setAuthToken(response.token);
                        await this.loadCurrentUser();
                        this.isLoggedIn = true;
                        this.loadDashboardData();
                    } else {
                        TransferCardAPI.clearAuthToken();
                    }
                } catch (error) {
                    TransferCardAPI.clearAuthToken();
                }
            }
        },
        
        // 加载当前用户信息
        async loadCurrentUser() {
            try {
                const response = await TransferCardAPI.user.getCurrentUser();
                if (response.success) {
                    this.currentUser = response.data;
                    console.log('用户信息已更新', response.data);
                } else {
                    console.error('用户信息获取失败:', response.message);
                }
            } catch (error) {
                console.error('加载用户信息失败:', error);
            }
        },
        
        // 登录
        async login() {
            try {
                console.log(' 开始登录流程..');
                const valid = await this.$refs.loginForm.validate();
                if (!valid) return;
                
                console.log(' 登录参数:', {
                    username: this.loginForm.username,
                    loginType: this.loginType,
                    department_id: this.loginForm.department_id
                });
                
                const response = await TransferCardAPI.auth.login(
                    this.loginForm.username,
                    this.loginForm.password,
                    this.loginType,
                    this.loginForm.department_id
                );
                
                console.log('📡 登录响应:', response);
                
                if (response.success) {
                    TransferCardAPI.setAuthToken(response.token);
                    console.log('Token已保存', response.token);
                    
                    this.currentUser = response.data;
                    console.log('用户信息已设置', this.currentUser);
                    
                    this.isLoggedIn = true;
                    console.log('登录状态已更新:', this.isLoggedIn);
                    
                    this.activeMenu = 'dashboard';
                    
                    this.loadDashboardData();
                    
                    console.log('登录成功！正在跳转..');
                    if (this.$message) {
                        this.$message.success('登录成功！正在跳转..');
                    }
                    
                    this.$nextTick(() => {
                        console.log('Vue视图已更新');
                        this.$forceUpdate();
                    });
                } else {
                    this.$message.error(response.message || '登录失败');
                }
            } catch (error) {
                console.error('登录失败:', error);
            }
        },
        
        // 退出登录
        async logout() {
            try {
                await TransferCardAPI.auth.logout();
            } catch (error) {
                console.error('退出登录失败', error);
            } finally {
                TransferCardAPI.clearAuthToken();
                this.isLoggedIn = false;
                this.currentUser = null;
                this.activeMenu = 'dashboard';
                this.$message.success('已退出登录');
            }
        },
        
        // 菜单选择处理
        handleMenuSelect(index) {
            if (index === 'logout') {
                this.logout();
            } else if (index === 'profile') {
                this.showProfile();
            } else {
                this.activeMenu = index;
                
                switch (index) {
                    case 'cards':
                        this.loadCards();
                        this.loadTemplateCards();
                        break;
                    case 'create-card':
                        this.loadTemplates();
                        break;
                    case 'user-management':
                        this.loadUsers();
                        this.loadDepartments();
                        break;
                    case 'department-management':
                        this.loadDepartments();
                        break;
                    case 'field-management':
                        this.loadFields();
                        break;
                    case 'template-management':
                        this.loadTemplates();
                        break;
                }
            }
        },
        
        // 加载工作台数据
        async loadDashboardData() {
            try {
                console.log(' 开始加载工作台数据...');
                
                // 调用后端API获取统计数据
                const response = await TransferCardAPI.dashboard.getStats();
                console.log('📡 工作台数据API响应:', response);
                
                if (response.success) {
                    this.dashboardData = response.data;
                    console.log(' 工作台数据加载成功:', this.dashboardData);
                } else {
                    console.error(' 工作台数据API返回失败:', response.message);
                    this.$message.error(response.message || '加载工作台数据失败');
                    
                    // 使用默认数据作为后备
                    this.dashboardData = {
                        pendingCards: 0,
                        completedToday: 0,
                        weeklyTotal: 0,
                        totalCards: 0,
                        pendingTrend: 'up',
                        pendingChange: 0,
                        completedTrend: 'up',
                        completedChange: 0,
                        weeklyTrend: 'up',
                        weeklyChange: 0,
                        totalTrend: 'up',
                        totalChange: 0
                    };
                }
                
                // 加载最近操作记录
                this.loadRecentOperations();
            } catch (error) {
                console.error(' 加载工作台数据失败:', error);
                this.$message.error('加载工作台数据失败，请检查网络连接');
                
                // 使用默认数据作为后备
                this.dashboardData = {
                    pendingCards: 0,
                    completedToday: 0,
                    weeklyTotal: 0,
                    totalCards: 0,
                    pendingTrend: 'up',
                    pendingChange: 0,
                    completedTrend: 'up',
                    completedChange: 0,
                    weeklyTrend: 'up',
                    weeklyChange: 0,
                    totalTrend: 'up',
                    totalChange: 0
                };
                
                // 仍然尝试加载操作记录
                this.loadRecentOperations();
            }
        },
        
        // 加载流转卡列表
        async loadCards() {
            try {
                const response = await TransferCardAPI.card.getCards();
                if (response.success) {
                    this.cards = response.data;
                }
            } catch (error) {
                console.error('加载流转卡列表失败', error);
            }
        },
        
        // 加载用户列表
        async loadUsers() {
            try {
                const response = await TransferCardAPI.user.getUsers();
                if (response.success) {
                    this.users = response.data;
                }
            } catch (error) {
                console.error('加载用户列表失败:', error);
            }
        },
        
        // 加载部门列表（需要认证）
        async loadDepartments() {
            try {
                const response = await TransferCardAPI.user.getDepartments();
                if (response.success) {
                    this.departments = response.data;
                }
            } catch (error) {
                console.error('加载部门列表失败:', error);
            }
        },
        
        // 加载公共部门列表（不需要认证，用于登录页面）
        async loadPublicDepartments() {
            try {
                const response = await axios.get('http://localhost:5000/api/public/departments');
                if (response.data.success) {
                    this.departments = response.data.data;
                }
            } catch (error) {
                console.error('加载公共部门列表失败:', error);
                this.departments = [
                    { id: 1, name: '研发部' },
                    { id: 2, name: '采购部' },
                    { id: 3, name: '销售部' },
                    { id: 4, name: '仓库部' }
                ];
            }
        },
        
        // 显示创建字段对话框（从预留字段选择）
        async showCreateFieldDialog() {
            this.isFieldEditMode = false;
            
            // 获取可用的预留字段
            try {
                const response = await TransferCardAPI.field.getAvailablePlaceholderFields();
                if (response.success && response.data.length > 0) {
                    // 使用第一个可用的预留字段
                    const placeholderField = response.data[0];
                    this.fieldForm = {
                        id: placeholderField.id,
                        name: placeholderField.name,
                        display_name: '',
                        field_type: placeholderField.field_type || 'text',
                        department_name: '',
                        category: '',
                        validation_rules: '',
                        options: placeholderField.options || '',
                        is_required: false,
                        is_hidden: false
                    };
                    this.fieldDialogVisible = true;
                } else {
                    this.$message.warning('暂无可用的预留字段，请先添加预留字段');
                }
            } catch (error) {
                console.error('获取预留字段失败:', error);
                this.$message.error('获取预留字段失败，请检查网络连接');
            }
        },

        // 编辑字段
        editField(field) {
            this.isFieldEditMode = true;
            this.fieldForm = { ...field };
            this.fieldDialogVisible = true;
        },

        // 保存字段
        async saveField() {
            try {
                let response;
                if (this.isFieldEditMode) {
                    response = await TransferCardAPI.field.updateField(this.fieldForm.id, this.fieldForm);
                } else {
                    // 新建字段时，需要传递field_id来指定要转换的预留字段
                    const fieldData = {
                        field_id: this.fieldForm.id, // 这是预留字段的ID
                        name: this.fieldForm.name,
                        display_name: this.fieldForm.display_name,
                        field_type: this.fieldForm.field_type,
                        department_name: this.fieldForm.department_name,
                        category: this.fieldForm.category,
                        validation_rules: this.fieldForm.validation_rules,
                        options: this.fieldForm.options,
                        is_required: this.fieldForm.is_required,
                        is_hidden: this.fieldForm.is_hidden
                    };
                    response = await TransferCardAPI.field.createField(fieldData);
                }
                
                if (response.success) {
                    this.$message.success(this.isFieldEditMode ? '更新成功' : '创建成功');
                    this.fieldDialogVisible = false;
                    this.loadFields();
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 删除字段
        async deleteField(field) {
            try {
                await this.$confirm('确定要删除该字段吗？', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                });
                
                const response = await TransferCardAPI.field.deleteField(field.id);
                if (response.success) {
                    this.$message.success('删除成功');
                    this.loadFields();
                } else {
                    this.$message.error(response.message || '删除失败');
                }
            } catch (error) {
                if (error !== 'cancel') {
                    this.$message.error('删除失败');
                }
            }
        },

        // 加载字段列表
        async loadFields() {
            try {
                console.log(' 开始加载字段列表..');
                const response = await TransferCardAPI.field.getFields();
                console.log(' 字段API响应:', response);
                
                if (response.success) {
                    this.fields = response.data || response.fields || [];
                    console.log('字段列表已加载', this.fields);
                    
                    this.$nextTick(() => {
                        this.$forceUpdate();
                    });
                } else {
                    console.error('字段API返回失败:', response.message);
                    this.$message.error(response.message || '加载字段列表失败');
                }
            } catch (error) {
                console.error('加载字段列表失败:', error);
                this.$message.error('加载字段列表失败，请检查网络连接');
            }
        },

        // 刷新字段列表
        refreshFields() {
            this.loadFields();
        },

        // 获取字段类型颜色
        getFieldTypeColor(type) {
            const colorMap = {
                'text': 'primary',
                'number': 'success',
                'date': 'warning',
                'select': 'info',
                'boolean': 'danger'
            };
            return colorMap[type] || 'info';
        },

        // 获取字段类型文本
        getFieldTypeText(type) {
            const typeMap = {
                'text': '文本',
                'number': '数字',
                'date': '日期',
                'select': '选择',
                'boolean': '布尔'
            };
            return typeMap[type] || type;
        },

        // ========== 模板管理方法 ==========

        // 加载模板列表
        async loadTemplates() {
            try {
                const response = await TransferCardAPI.template.getTemplates();
                if (response.success) {
                    const templates = response.data.map(template => ({
                        ...template,
                        is_active: template.is_active === 1 || template.is_active === true
                    }));
                    
                    this.templates = templates;
                    
                    console.log('模板列表已加载，状态已初始化', templates.map(t => ({
                        name: t.template_name,
                        is_active: t.is_active,
                        type: typeof t.is_active
                    })));
                } else {
                    this.$message.error(response.message || '加载模板列表失败');
                }
            } catch (error) {
                console.error('加载模板列表失败:', error);
                this.$message.error('加载模板列表失败，请检查网络连接');
            }
        },

        // 刷新模板列表
        refreshTemplates() {
            this.loadTemplates();
        },

        // 显示创建模板对话框
        showCreateTemplateDialog() {
            this.isTemplateEditMode = false;
            this.templateForm = {
                id: null,
                template_name: '',
                template_description: '',
                is_active: true
            };
            this.templateDialogVisible = true;
        },

        // 编辑模板
        editTemplate(template) {
            this.isTemplateEditMode = true;
            const convertedIsActive = template.is_active === 1 || template.is_active === true;
            
            this.templateForm = {
                ...template,
                is_active: convertedIsActive
            };
            
            this.templateDialogVisible = true;
        },

        // 保存模板
        async saveTemplate() {
            try {
                let response;
                if (this.isTemplateEditMode) {
                    response = await TransferCardAPI.template.updateTemplate(this.templateForm.id, this.templateForm);
                } else {
                    response = await TransferCardAPI.template.createTemplate(this.templateForm);
                }
                
                if (response.success) {
                    this.$message.success(this.isTemplateEditMode ? '更新成功' : '创建成功');
                    this.templateDialogVisible = false;
                    this.loadTemplates();
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                console.error('保存模板失败:', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 删除模板
        async deleteTemplate(template) {
            try {
                await this.$confirm('确定要删除该模板吗？', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                });
                
                const response = await TransferCardAPI.template.deleteTemplate(template.id);
                if (response.success) {
                    this.$message.success('删除成功');
                    this.loadTemplates();
                } else {
                    this.$message.error(response.message || '删除失败');
                }
            } catch (error) {
                if (error !== 'cancel') {
                    this.$message.error('删除失败');
                }
            }
        },

        // 处理模板状态变更
        async handleStatusChange(template) {
            if (this.statusUpdating) {
                this.$message.warning('状态更新中，请稍候..');
                return;
            }
            
            this.statusUpdating = true;
            const originalStatus = template.is_active;
            
            try {
                console.log(' 状态变更 - 模板:', template.template_name, '新状态:', template.is_active);
                
                const response = await TransferCardAPI.template.updateTemplate(template.id, {
                    is_active: template.is_active
                });
                
                if (response.success) {
                    this.$message.success(template.is_active ? '已启用' : '已禁用');
                    await this.loadTemplates();
                } else {
                    this.$set(template, 'is_active', !originalStatus);
                    this.$message.error(response.message || '状态更新失败');
                }
            } catch (error) {
                this.$set(template, 'is_active', !originalStatus);
                console.error('状态更新失败', error);
                this.$message.error('状态更新失败，请检查网络连接');
            } finally {
                this.statusUpdating = false;
            }
        },

        // 管理模板字段
        async manageTemplateFields(template) {
            this.currentTemplate = { ...template };
            await this.loadAllFieldsForTemplate();
            await this.loadTemplateFields(template.id);
            this.templateFieldDialogVisible = true;
        },

        // 加载模板字段
        async loadTemplateFields(templateId) {
            try {
                const response = await TransferCardAPI.template.getTemplateFields(templateId);
                if (response.success) {
                    this.templateFields = response.data;
                } else {
                    this.$message.error(response.message || '加载模板字段失败');
                }
            } catch (error) {
                console.error('加载模板字段失败:', error);
                this.$message.error('加载模板字段失败，请检查网络连接');
            }
        },

        // 加载所有字段用于模板管理
        async loadAllFieldsForTemplate() {
            try {
                const response = await TransferCardAPI.field.getFields();
                if (response.success) {
                    this.allFieldsForTemplate = response.data || [];
                    
                    const templateFieldNames = this.templateFields.map(tf => tf.field_name);
                    this.allFieldsForTemplate.forEach(field => {
                        this.$set(field, 'selected', templateFieldNames.includes(field.name));
                    });
                    
                    this.updateFilteredTemplateFields();
                } else {
                    this.$message.error(response.message || '加载字段列表失败');
                }
            } catch (error) {
                console.error('加载字段列表失败:', error);
                this.$message.error('加载字段列表失败，请检查网络连接');
            }
        },

        // 更新筛选后的模板字段（隐藏预留字段）
        updateFilteredTemplateFields() {
            let filtered = this.allFieldsForTemplate || [];
            
            // 隐藏预留字段
            filtered = filtered.filter(field => !field.is_placeholder);
            
            if (this.fieldSearchKeyword) {
                const keyword = this.fieldSearchKeyword.toLowerCase();
                filtered = filtered.filter(field => 
                    field.name.toLowerCase().includes(keyword) ||
                    field.display_name.toLowerCase().includes(keyword)
                );
            }
            
            if (this.fieldDepartmentFilter) {
                filtered = filtered.filter(field => {
                    if (this.fieldDepartmentFilter === '未分类') {
                        return !field.department_name || field.department_name === '';
                    }
                    return field.department_name === this.fieldDepartmentFilter;
                });
            }
            
            if (this.fieldTypeFilter) {
                filtered = filtered.filter(field => field.field_type === this.fieldTypeFilter);
            }
            
            this.filteredTemplateFields = filtered;
            this.updateSelectAllState();
        },

        // 更新全选状态
        updateSelectAllState() {
            if (!this.filteredTemplateFields || this.filteredTemplateFields.length === 0) {
                this.selectAllFields = false;
                this.isSelectAllIndeterminate = false;
                return;
            }
            
            const selectedCount = this.filteredTemplateFields.filter(field => field.selected).length;
            const totalCount = this.filteredTemplateFields.length;
            
            this.selectAllFields = selectedCount === totalCount;
            this.isSelectAllIndeterminate = selectedCount > 0 && selectedCount < totalCount;
        },

        // 处理全选变化
        handleSelectAllChange(value) {
            this.filteredTemplateFields.forEach(field => {
                this.$set(field, 'selected', value);
            });
        },

        // 处理单个字段选择变化
        handleFieldSelectionChange(field) {
            this.updateSelectAllState();
        },

        // 保存模板字段配置
        async saveTemplateFields() {
            try {
                const selectedFields = this.allFieldsForTemplate.filter(field => field.selected);
                
                if (selectedFields.length === 0) {
                    this.$message.warning('请至少选择一个字段');
                    return;
                }
                
                const templateFieldData = selectedFields.map((field, index) => ({
                    template_id: this.currentTemplate.id,
                    field_name: field.name,
                    field_order: index + 1,
                    is_required: field.is_required || false,
                    default_value: ''
                }));
                
                const response = await TransferCardAPI.template.updateTemplateFields(this.currentTemplate.id, templateFieldData);
                
                if (response.success) {
                    this.$message.success('字段配置保存成功');
                    this.templateFieldDialogVisible = false;
                    this.loadTemplates();
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                console.error('保存模板字段失败:', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // ========== 基于模板创建流转卡方法 ==========

        // 基于模板创建流转卡
        async createCardFromTemplate(template) {
            this.currentTemplate = { ...template };
            await this.loadTemplateFieldsForCard(template.id);
            
            this.templateCardForm = {
                card_number: '',
                template_id: template.id,
                title: '',
                description: '',
                row_count: 5,
                responsible_person: '',
                create_date: new Date(),
                status: 'draft',
                field_data: {}
            };
            
            // 初始化字段选择状态和数据
            this.currentTemplateFields.forEach(field => {
                this.$set(field, 'selected', false); // 默认不选中
                this.$set(field, 'default_value', field.default_value || '');
                this.$set(this.templateCardForm.field_data, field.name, field.default_value || '');
            });
            
            // 初始化预览表格数据
            this.updatePreviewTableData();
            this.updateSelectAllTemplateFieldsState();
            
            this.createCardFromTemplateDialogVisible = true;
        },

        // 加载模板字段用于创建流转卡
        async loadTemplateFieldsForCard(templateId) {
            try {
                const response = await TransferCardAPI.template.getTemplateFields(templateId);
                if (response.success) {
                    this.currentTemplateFields = response.data.map(field => {
                        // 处理选项数据
                        if (field.options) {
                            try {
                                if (typeof field.options === 'string') {
                                    field.options = JSON.parse(field.options);
                                }
                            } catch (e) {
                                field.options = [];
                            }
                        } else {
                            field.options = [];
                        }
                        return field;
                    });
                } else {
                    this.$message.error(response.message || '加载模板字段失败');
                }
            } catch (error) {
                console.error('加载模板字段失败:', error);
                this.$message.error('加载模板字段失败，请检查网络连接');
            }
        },

        // 保存模板流转卡
        async saveTemplateCard() {
            try {
                // 验证必填字段
                for (const field of this.currentTemplateFields) {
                    if (field.is_required && !this.templateCardForm.field_data[field.name]) {
                        this.$message.error(`请填写必填字段：${field.field_display_name}`);
                        return;
                    }
                }

                const response = await TransferCardAPI.template.createTemplateCard(this.templateCardForm);
                
                if (response.success) {
                    this.$message.success('流转卡创建成功');
                    this.createCardFromTemplateDialogVisible = false;
                    this.loadCards(); // 刷新流转卡列表
                } else {
                    this.$message.error(response.message || '创建失败');
                }
            } catch (error) {
                console.error('创建流转卡失败', error);
                this.$message.error('创建失败，请检查网络连接');
            }
        },

        // 检查字段权限
        canEditField(field) {
            if (!this.currentUser || this.currentUser.role === 'admin') {
                return true;
            }
            return field.department_name === this.currentUser.department_name;
        },

        // 检查字段权限并返回权限信息
        getFieldPermissionInfo(field) {
            if (!this.currentUser) {
                return { canEdit: false, text: '未登录', type: 'danger' };
            }
            
            if (this.currentUser.role === 'admin') {
                return { canEdit: true, text: '管理员可编辑', type: 'success' };
            }
            
            if (field.department_name === this.currentUser.department_name) {
                return { canEdit: true, text: '您的部门可编辑', type: 'success' };
            }
            
            return { 
                canEdit: false, 
                text: `${field.department_name || '未分配部门'} 专用`,
                type: 'warning' 
            };
        },

        // 获取字段权限文本
        getFieldPermissionText(field) {
            if (this.currentUser && this.currentUser.role === 'admin') {
                return '管理员';
            }
            if (field.department_name === this.currentUser.department_name) {
                return '可编辑';
            }
            return '只读';
        },

        // ========== 流转卡表格格式显示方法 ==========

        // 加载基于模板的流转卡列表
        async loadTemplateCards() {
            try {
                const response = await TransferCardAPI.template.getTemplateCards();
                if (response.success) {
                    this.templateCards = response.data;
                } else {
                    this.$message.error(response.message || '加载模板流转卡失败');
                }
            } catch (error) {
                console.error('加载模板流转卡失败', error);
                this.$message.error('加载模板流转卡失败，请检查网络连接');
            }
        },

        // 查看模板流转卡详情
        async viewTemplateCard(card) {
            this.currentTemplateCard = { ...card };
            await this.loadTemplateCardData(card.id);
            this.generateTableFormat();
        },

        // 加载流转卡详情数据（使用新的API）
        async loadTemplateCardData(cardId) {
            try {
                const response = await TransferCardAPI.card.getCardData(cardId);
                if (response.success) {
                    const data = response.data;
                    this.currentTemplateCardData = data.table_data || [];
                    this.fields = data.fields || [];
                    this.generateUniqueDepartments();
                    this.generateCardDataRows();
                } else {
                    this.$message.error(response.message || '加载流转卡详情失败');
                }
            } catch (error) {
                console.error('加载流转卡详情失败', error);
                this.$message.error('加载流转卡详情失败，请检查网络连接');
            }
        },

        // 生成唯一部门列表
        generateUniqueDepartments() {
            const departments = new Set();
            
            // 从模板字段中获取部门
            if (this.currentTemplateCard && this.currentTemplateCard.template_name) {
                // 这里应该从模板信息中获取部门，简化处理
                departments.add('研发部');
                departments.add('采购部');
                departments.add('销售部');
                departments.add('生产部');
                departments.add('质检部');
                departments.add('仓库部');
            }
            
            this.uniqueDepartments = Array.from(departments).map(name => ({ name }));
        },

        // 生成表格格式数据
        generateTableFormat() {
            if (!this.currentTemplateCardData || !this.currentTemplateFields) return;
            
            // 生成表头数据行
            this.currentTemplateCardData = this.currentTemplateFields.map(field => {
                const deptFields = {};
                this.uniqueDepartments.forEach(dept => {
                    deptFields[dept.name] = field.department_name === dept.name ? field.display_name || field.name : '';
                });
                
                return {
                    fieldName: field.display_name || field.name,
                    ...deptFields
                };
            });
        },

        // 生成数据填写行
        generateCardDataRows() {
            this.cardDataRows = [
                { rowType: 'data' },
                { rowType: 'data' },
                { rowType: 'data' }
            ];
            
            // 初始化每行的部门数据
            this.cardDataRows.forEach(row => {
                this.uniqueDepartments.forEach(dept => {
                    row[dept.name] = '';
                });
            });
        },

        // 检查是否可以编辑当前流转卡
        canEditCurrentCard() {
            if (!this.currentTemplateCard || !this.currentUser) return false;
            // 管理员可以编辑所有流转卡
            if (this.currentUser.role === 'admin') return true;
            // 普通用户可以编辑所有流转卡（但只能编辑自己部门的字段）
            return true;
        },

        // 检查是否可以编辑部门字段
        canEditDepartmentField(departmentName) {
            if (!this.currentUser) return false;
            if (this.currentUser.role === 'admin') return true;
            return departmentName === this.currentUser.department_name;
        },

        // 编辑模板流转卡
        async editTemplateCard(card) {
            this.currentTemplateCard = { ...card };
            await this.loadTemplateCardData(card.id);
            this.generateTableFormat();
        },

        // 删除模板流转卡
        async deleteTemplateCard(card) {
            try {
                await this.$confirm('确定要删除该流转卡吗？', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                });
                
                const response = await TransferCardAPI.template.deleteTemplateCard(card.id);
                if (response.success) {
                    this.$message.success('删除成功');
                    this.loadTemplateCards();
                } else {
                    this.$message.error(response.message || '删除失败');
                }
            } catch (error) {
                if (error !== 'cancel') {
                    this.$message.error('删除失败');
                }
            }
        },

        // 保存数据行
        async saveCardDataRow(row) {
            try {
                if (!this.currentTemplateCard || !this.currentTemplateCard.id) {
                    this.$message.error('流转卡信息不完整');
                    return;
                }
                
                // 准备要保存的数据
                const rowData = {
                    row_data: [row] // 将单行数据包装成数组格式
                };
                
                console.log('保存数据行', rowData);
                
                const response = await TransferCardAPI.card.saveCardData(this.currentTemplateCard.id, rowData);
                
                if (response.success) {
                    this.$message.success('数据保存成功');
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                console.error('保存数据行失败', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 显示创建流转卡对话框
        showCreateCardDialog() {
            if (this.isAdmin) {
                this.$message.info('请通过模板管理页面创建流转卡');
            } else {
                this.$message.warning('只有管理员可以创建流转卡');
            }
        },

        // 刷新流转卡
        refreshCards() {
            this.loadCards();
            this.loadTemplateCards();
        },

        // 获取状态文本
        getStatusText(status) {
            const statusMap = {
                'draft': '草稿',
                'in_progress': '进行中',
                'completed': '已完成',
                'cancelled': '已取消'
            };
            return statusMap[status] || status;
        },

        // 获取状态类型
        getStatusType(status) {
            const typeMap = {
                'draft': 'warning',
                'in_progress': 'primary',
                'completed': 'success',
                'cancelled': 'danger'
            };
            return typeMap[status] || 'info';
        },

        // 检查是否可以编辑流转卡
        canEditCard(card) {
            if (!this.currentUser) return false;
            
            // 已完成的流转卡不能编辑（管理员除外）
            if (card.status === 'completed' || card.status === 'cancelled') {
                return this.currentUser.role === 'admin';
            }
            
            // 管理员可以编辑所有流转卡
            if (this.currentUser.role === 'admin') return true;
            // 普通用户可以填写数据
            return true;
        },

        // 检查是否可以重启流转卡（仅管理员）
        canRestartCard(card) {
            if (!this.currentUser) return false;
            // 只有管理员可以重启流转卡
            if (this.currentUser.role !== 'admin') return false;
            // 只有已完成或已驳回的流转卡可以重启
            return card.status === 'completed' || card.status === 'rejected';
        },

        // 管理员重启流转卡
        async restartCard(card) {
            try {
                if (!this.currentUser || this.currentUser.role !== 'admin') {
                    this.$message.warning('只有管理员可以重启流转卡');
                    return;
                }

                await this.$confirm('确定要重启此流转卡吗？\n重启后，流转卡将重新开始流转，当前进度将被重置。', '确认重启', {
                    confirmButtonText: '确定重启',
                    cancelButtonText: '取消',
                    type: 'warning'
                });

                // 询问要流转到哪个部门
                const { value: departmentId } = await this.$prompt('请输入要流转到的部门ID（留空则流转到第一个部门）', '选择流转部门', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    inputPlaceholder: '例如：1'
                });

                const restartData = {};
                if (departmentId && departmentId.trim() !== '') {
                    restartData.department_id = parseInt(departmentId.trim());
                }

                console.log(' 重启流转卡:', {
                    cardId: card.id,
                    departmentId: restartData.department_id
                });

                const response = await TransferCardAPI.flow.restartCardFlow(card.id, restartData);

                if (response.success) {
                    this.$message.success(response.message || '流转卡已重启');
                    this.loadTemplateCards();
                } else {
                    this.$message.error(response.message || '重启失败');
                }
            } catch (error) {
                if (error !== 'cancel') {
                    console.error(' 重启流转卡失败:', error);
                    this.$message.error('重启失败，请检查网络连接');
                }
            }
        },

        // 检查是否可以删除流转卡
        canDeleteCard(card) {
            if (!this.currentUser) return false;
            // 管理员可以删除所有流转卡
            if (this.currentUser.role === 'admin') return true;
            // 普通用户不能删除流转卡
            return false;
        },

        // 检查是否可以创建流转卡
        canCreateCard() {
            if (!this.currentUser) return false;
            // 管理员可以创建流转卡
            if (this.currentUser.role === 'admin') return true;
            // 普通用户也可以创建流转卡
            return true;
        },

        // 查看流转卡详情
        viewCard(card) {
            console.log('查看流转卡', card);
            this.$message.info('流转卡详情功能开发中...');
        },

        // 编辑流转卡
        editCard(card) {
            console.log('编辑流转卡', card);
            // 调用editCardData方法来打开编辑对话框
            this.editCardData(card);
        },

        // 显示个人信息
        showProfile() {
            this.$message.info('个人信息功能开发中...');
        },

        // ========== 补充缺失的方法 ==========

        // 保存流转卡
        async saveCard() {
            try {
                console.log('保存流转卡', this.cardForm);
                this.$message.success('流转卡保存成功');
                this.cardDialogVisible = false;
            } catch (error) {
                console.error('保存流转卡失败', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 保存用户
        async saveUser() {
            try {
                let response;
                if (this.isUserEditMode) {
                    response = await TransferCardAPI.user.updateUser(this.userForm.id, this.userForm);
                } else {
                    response = await TransferCardAPI.user.createUser(this.userForm);
                }
                
                if (response.success) {
                    this.$message.success(this.isUserEditMode ? '更新成功' : '创建成功');
                    this.userDialogVisible = false;
                    this.loadUsers();
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                console.error('保存用户失败:', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 保存部门 - 修复版本
        async saveDepartment() {
            try {
                console.log(' 开始保存部门:', this.departmentForm);
                
                let response;
                if (this.isDepartmentEditMode) {
                    // 使用正确的API调用方式
                    response = await TransferCardAPI.user.updateDepartment(this.departmentForm.id, this.departmentForm);
                } else {
                    // 使用正确的API调用方式
                    response = await TransferCardAPI.user.createDepartment(this.departmentForm);
                }
                
                console.log('📡 部门保存响应:', response);
                
                if (response.success) {
                    this.$message.success(this.isDepartmentEditMode ? '更新成功' : '创建成功');
                    this.departmentDialogVisible = false;
                    this.loadDepartments();
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                console.error(' 保存部门失败:', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 刷新模板字段
        refreshTemplateFields() {
            this.loadAllFieldsForTemplate();
        },

        // 显示创建用户对话框
        showCreateUserDialog() {
            this.isUserEditMode = false;
            this.userForm = {
                id: null,
                username: '',
                password: '',
                real_name: '',
                email: '',
                department_id: null,
                role: 'user'
            };
            this.userDialogVisible = true;
        },

        // 编辑用户
        editUser(user) {
            this.isUserEditMode = true;
            this.userForm = { ...user };
            this.userDialogVisible = true;
        },

        // 删除用户
        async deleteUser(user) {
            try {
                await this.$confirm('确定要删除该用户吗？', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                });
                
                const response = await TransferCardAPI.user.deleteUser(user.id);
                if (response.success) {
                    this.$message.success('删除成功');
                    this.loadUsers();
                } else {
                    this.$message.error(response.message || '删除失败');
                }
            } catch (error) {
                if (error !== 'cancel') {
                    this.$message.error('删除失败');
                }
            }
        },

        // 显示创建部门对话框
        showCreateDepartmentDialog() {
            this.isDepartmentEditMode = false;
            this.departmentForm = {
                id: null,
                name: '',
                description: ''
            };
            this.departmentDialogVisible = true;
        },

        // 编辑部门
        editDepartment(department) {
            this.isDepartmentEditMode = true;
            this.departmentForm = { ...department };
            this.departmentDialogVisible = true;
        },

        // 删除部门 - 修复版本
        async deleteDepartment(department) {
            try {
                await this.$confirm('确定要删除该部门吗？', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                });
                
                // 使用正确的API调用方式
                const response = await TransferCardAPI.user.deleteDepartment(department.id);
                if (response.success) {
                    this.$message.success('删除成功');
                    this.loadDepartments();
                } else {
                    this.$message.error(response.message || '删除失败');
                }
            } catch (error) {
                if (error !== 'cancel') {
                    this.$message.error('删除失败');
                }
            }
        },

        // 查看字段详情
        viewFieldDetails(field) {
            console.log('查看字段详情:', field);
            this.$message.info(`字段详情: ${field.display_name} (${field.name})`);
        },

        // ========== 表格格式对话框相关方法 ==========

        // 处理模板字段全选变化
        handleSelectAllTemplateFieldsChange(value) {
            this.currentTemplateFields.forEach(field => {
                this.$set(field, 'selected', value);
            });
            this.updatePreviewTableData();
        },

        // 处理单个模板字段选择变化
        handleTemplateFieldSelectionChange(field) {
            this.updateSelectAllTemplateFieldsState();
            this.updatePreviewTableData();
        },

        // 更新模板字段全选状态
        updateSelectAllTemplateFieldsState() {
            if (!this.currentTemplateFields || this.currentTemplateFields.length === 0) {
                this.selectAllTemplateFields = false;
                this.isSelectAllTemplateFieldsIndeterminate = false;
                return;
            }
            
            const selectedCount = this.currentTemplateFields.filter(field => field.selected).length;
            const totalCount = this.currentTemplateFields.length;
            
            this.selectAllTemplateFields = selectedCount === totalCount;
            this.isSelectAllTemplateFieldsIndeterminate = selectedCount > 0 && selectedCount < totalCount;
        },

        // 获取字段预览宽度
        getFieldPreviewWidth(field) {
            const widthMap = {
                'text': '200',
                'number': '150',
                'date': '180',
                'select': '150',
                'boolean': '100'
            };
            return widthMap[field.field_type] || '150';
        },

        // 更新预览表格数据（简化版，用于预览显示）
        updatePreviewTableData() {
            const selectedFields = this.selectedTemplateFieldsForPreview;
            
            console.log(' 更新表格结构预览，选中字段数量:', selectedFields.length);
            console.log(' 选中字段:', selectedFields);
            
            // 预览模式不需要真实数据，只生成空行用于显示结构
            this.previewTableData = [{}];
            
            console.log(' 表格结构预览已生成，字段数量:', selectedFields.length);
            
            // 强制更新视图
            this.$nextTick(() => {
                this.$forceUpdate();
            });
        },

        // 保存表格格式的模板流转卡
        async saveTemplateCardWithTableData() {
            try {
                // 验证基本信息
                if (!this.templateCardForm.card_number) {
                    this.$message.error('请输入流转卡号');
                    return;
                }
                
                if (!this.templateCardForm.title) {
                    this.$message.error('请输入流转卡标题');
                    return;
                }

                // 验证选择的字段
                const selectedFields = this.selectedTemplateFieldsForPreview;
                if (selectedFields.length === 0) {
                    this.$message.error('请至少选择一个字段作为表格列');
                    return;
                }

                // 验证必填字段
                for (const field of selectedFields) {
                    if (field.is_required) {
                        const hasValue = this.previewTableData.some(row => row[field.name]);
                        if (!hasValue) {
                            this.$message.error(`必填字段 "${field.display_name || field.name}" 至少需要在一行中填写数据`);
                            return;
                        }
                    }
                }

                // 准备保存数据
                const cardData = {
                    template_id: this.templateCardForm.template_id,
                    card_number: this.templateCardForm.card_number,
                    title: this.templateCardForm.title,
                    description: this.templateCardForm.description,
                    row_count: this.templateCardForm.row_count,
                    responsible_person: this.templateCardForm.responsible_person,
                    create_date: this.templateCardForm.create_date,
                    status: this.templateCardForm.status,
                    selected_fields: selectedFields.map(field => ({
                        field_name: field.name,
                        field_display_name: field.display_name || field.name,
                        field_type: field.field_type,
                        is_required: field.is_required,
                        default_value: field.default_value || '',
                        department_name: field.department_name
                    })),
                    table_data: this.previewTableData
                };

                const response = await TransferCardAPI.template.createTemplateCardWithTableData(cardData);
                
                if (response.success) {
                    this.$message.success('表格格式流转卡创建成功');
                    this.createCardFromTemplateDialogVisible = false;
                    this.loadTemplateCards(); // 刷新流转卡列表
                } else {
                    this.$message.error(response.message || '创建失败');
                }
            } catch (error) {
                console.error('创建表格格式流转卡失败', error);
                this.$message.error('创建失败，请检查网络连接');
            }
        },

        // ========== 新增的流转卡管理方法 ==========

        // 格式化日期时间
        formatDateTime(dateTime) {
            if (!dateTime) return '';
            try {
                const date = new Date(dateTime);
                return date.toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (error) {
                return dateTime;
            }
        },

        // 查看流转卡详情
        async viewCardDetail(card) {
            try {
                this.currentCardDetail = { ...card };
                this.cardDetailDialogVisible = true;
                
                // 设置查看模式标志
                this.isViewMode = true;
                
                // 加载流转卡详细数据
                await this.loadCardDetailData(card.id);
            } catch (error) {
                console.error('加载流转卡详情失败:', error);
                this.$message.error('加载流转卡详情失败');
            }
        },

        // 加载流转卡详细数据
        async loadCardDetailData(cardId) {
            try {
                const response = await TransferCardAPI.card.getCardData(cardId);
                if (response.success) {
                    const data = response.data;
                    this.cardDetailFields = data.fields || [];
                    this.cardDataTable = data.table_data || [];
                    
                    // 确保每行都有所有字段的初始化值
                    this.cardDataTable = this.cardDataTable.map(row => {
                        const newRow = { ...row };
                        this.cardDetailFields.forEach(field => {
                            if (!(field.name in newRow)) {
                                newRow[field.name] = '';
                            }
                        });
                        return newRow;
                    });
                    
                    // 生成带部门行的表格数据
                    this.generateCardDataTableWithDepartment();
                } else {
                    this.$message.error(response.message || '加载流转卡数据失败');
                }
            } catch (error) {
                console.error('加载流转卡数据失败:', error);
                this.$message.error('加载流转卡数据失败，请检查网络连接');
            }
        },

        // 不再需要生成部门行，直接使用cardDataTable
        generateCardDataTableWithDepartment() {
            // 直接使用cardDataTable，部门信息现在显示在表头上方
            this.cardDataTableWithDepartment = this.cardDataTable;
        },

        // 获取字段列的CSS类名
        getFieldColumnClass(field) {
            if (!this.currentUser || this.currentUser.role === 'admin') {
                return '';
            }
            
            // 如果字段不属于当前用户部门，添加淡灰色样式
            if (field.department_name !== this.currentUser.department_name) {
                return 'non-department-field';
            }
            
            return '';
        },

        // 编辑流转卡数据
        async editCardData(card) {
            try {
                console.log(' 开始编辑流转卡数据:', card);
                
                this.currentEditingCard = { ...card };
                this.cardDataEditForm = {
                    status: card.status,
                    table_data: []
                };
                
                // 加载流转卡字段和数据
                await this.loadCardEditData(card.id);
                
                this.cardDataEditDialogVisible = true;
                
                console.log(' 流转卡编辑对话框已打开');
                console.log('📊 当前编辑的流转卡ID:', card.id);
                
            } catch (error) {
                console.error(' 加载编辑数据失败:', error);
                this.$message.error('加载编辑数据失败');
            }
        },

        // 加载流转卡编辑数据
        async loadCardEditData(cardId) {
            try {
                const response = await TransferCardAPI.card.getCardData(cardId);
                if (response.success) {
                    const data = response.data;
                    this.cardDataEditFields = data.fields || [];
                    this.cardDataEditForm.table_data = data.table_data || [];
                    
                    // 确保每行都有所有字段的初始化值
                    this.cardDataEditForm.table_data = this.cardDataEditForm.table_data.map(row => {
                        const newRow = { ...row };
                        this.cardDataEditFields.forEach(field => {
                            if (!(field.name in newRow)) {
                                newRow[field.name] = '';
                            }
                        });
                        return newRow;
                    });
                } else {
                    this.$message.error(response.message || '加载流转卡数据失败');
                }
            } catch (error) {
                console.error('加载流转卡数据失败:', error);
                this.$message.error('加载流转卡数据失败，请检查网络连接');
            }
        },

        // 保存流转卡数据编辑
        async saveCardDataEdit() {
            try {
                if (!this.currentEditingCard || !this.currentEditingCard.id) {
                    this.$message.error('流转卡信息不完整');
                    return;
                }

                const updateData = {
                    status: this.cardDataEditForm.status,
                    table_data: this.cardDataEditForm.table_data
                };

                // 如果启用了协作，先广播变化
                if (this.isCollaborationEnabled) {
                    this.broadcastDataChange('save_pending', updateData);
                }

                const response = await TransferCardAPI.card.updateCardData(this.currentEditingCard.id, updateData);
                
                if (response.success) {
                    this.$message.success('数据保存成功');
                    
                    // 如果启用了协作，通知其他用户数据已保存
                    if (this.isCollaborationEnabled) {
                        this.broadcastDataChange('save_complete', {
                            timestamp: new Date().toISOString(),
                            data: updateData
                        });
                    }
                    
                    this.cardDataEditDialogVisible = false;
                    this.loadTemplateCards(); // 刷新列表
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                console.error('保存流转卡数据失败:', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 保存流转卡详情数据
        async saveCardData() {
            try {
                if (!this.currentCardDetail || !this.currentCardDetail.id) {
                    this.$message.error('流转卡信息不完整');
                    return;
                }

                // 直接使用cardDataTable，不再需要过滤部门行
                const updateData = {
                    table_data: this.cardDataTable
                };

                const response = await TransferCardAPI.card.updateCardData(this.currentCardDetail.id, updateData);
                
                if (response.success) {
                    this.$message.success('数据保存成功');
                    // 重新加载数据
                    await this.loadCardDetailData(this.currentCardDetail.id);
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                console.error('保存流转卡数据失败:', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 添加新行
        addNewRow() {
            const newRow = {};
            this.cardDetailFields.forEach(field => {
                newRow[field.name] = '';
            });
            this.cardDataTable.push(newRow);
        },

        // 删除行
        deleteRow(index) {
            if (this.cardDataTable.length > 1) {
                this.cardDataTable.splice(index, 1);
            } else {
                this.$message.warning('至少需要保留一行数据');
            }
        },

        // 获取字段列宽度
        getFieldColumnWidth(field) {
            const widthMap = {
                'text': 200,
                'number': 150,
                'date': 180,
                'select': 150,
                'boolean': 100
            };
            return widthMap[field.field_type] || 150;
        },

        // 获取字段选项
        getFieldOptions(field) {
            if (!field.options) return [];
            try {
                if (typeof field.options === 'string') {
                    return JSON.parse(field.options);
                }
                return Array.isArray(field.options) ? field.options : [];
            } catch (error) {
                console.error('解析字段选项失败:', error);
                return [];
            }
        },

        // 格式化字段值显示
        formatFieldValue(value, fieldType) {
            // console.log(` 格式化字段值:`, { value, fieldType, valueType: typeof value });
            
            if (value === null || value === undefined) {
                return '';
            }
            
            // 处理空字符串
            if (value === '') {
                return '';
            }
            
            // 处理数字类型
            if (fieldType === 'number') {
                if (typeof value === 'number') {
                    // 如果是0，显示为0.0000
                    return value === 0 ? '0.0000' : value.toString();
                } else if (typeof value === 'string') {
                    // 如果是字符串，尝试转换为数字
                    const num = parseFloat(value);
                    if (!isNaN(num)) {
                        return num === 0 ? '0.0000' : num.toString();
                    }
                    return value;
                } else if (typeof value.toString === 'function') {
                    // 处理Decimal类型（来自数据库的DECIMAL类型）
                    const strValue = value.toString();
                    const num = parseFloat(strValue);
                    if (!isNaN(num)) {
                        return num === 0 ? '0.0000' : strValue;
                    }
                    return strValue;
                }
                return String(value);
            }
            
            // 处理日期类型
            if (fieldType === 'date') {
                if (value && typeof value === 'object') {
                    if (value.toISOString) {
                        // Date对象
                        return value.toISOString().split('T')[0];
                    } else if (value.getFullYear) {
                        // 另一种Date对象
                        return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
                    }
                }
                if (typeof value === 'string' && value) {
                    // 如果已经是字符串格式，直接返回
                    return value;
                }
            }
            
            // 默认返回字符串
            return String(value);
        },

        // 获取字段显示值（用于表格显示）
        getFieldDisplayValue(row, field) {
            const value = row[field.name];
            return this.formatFieldValue(value, field.field_type);
        },

        // ========== 快速创建流转卡方法 ==========

        // 计算属性：启用的模板列表
        activeTemplates() {
            return this.templates.filter(template => 
                template.is_active === 1 || template.is_active === true
            );
        },

        // 计算属性：选中模板的字段列表
        selectedTemplateFields() {
            if (!this.selectedTemplate) return [];
            // 这里应该从模板字段中获取，简化处理
            return this.fields.filter(field => !field.is_placeholder).slice(0, 5);
        },

        // 选择模板
        selectTemplate(template) {
            this.selectedTemplate = template;
            console.log('选择模板:', template);
        },

        // 下一步
        nextStep() {
            if (this.createCardStep === 0) {
                // 验证是否选择了模板
                if (!this.selectedTemplate) {
                    this.$message.warning('请选择一个模板');
                    return;
                }
            } else if (this.createCardStep === 1) {
                // 验证表单
                this.$refs.quickCreateForm.validate((valid) => {
                    if (valid) {
                        this.createCardStep++;
                    } else {
                        this.$message.error('请填写完整信息');
                    }
                });
                return;
            }
            
            this.createCardStep++;
        },

        // 上一步
        prevStep() {
            if (this.createCardStep > 0) {
                this.createCardStep--;
            }
        },

        // 确认创建流转卡
        async confirmCreateCard() {
            try {
                this.creatingCard = true;
                
                // 准备创建数据
                const cardData = {
                    template_id: this.selectedTemplate.id,
                    card_number: this.quickCreateForm.card_number,
                    title: this.quickCreateForm.title,
                    description: this.quickCreateForm.description,
                    responsible_person: this.quickCreateForm.responsible_person,
                    row_count: this.quickCreateForm.row_count,
                    create_date: this.quickCreateForm.create_date,
                    status: this.quickCreateForm.status
                };

                console.log('创建流转卡数据:', cardData);

                // 调用API创建流转卡
                const response = await TransferCardAPI.template.createTemplateCard(cardData);
                
                if (response.success) {
                    this.$message.success('流转卡创建成功！');
                    
                    // 重置表单和步骤
                    this.resetQuickCreateForm();
                    
                    // 跳转到流转卡管理页面
                    this.activeMenu = 'cards';
                    this.loadTemplateCards();
                    
                } else {
                    this.$message.error(response.message || '创建失败');
                }
            } catch (error) {
                console.error('创建流转卡失败:', error);
                this.$message.error('创建失败，请检查网络连接');
            } finally {
                this.creatingCard = false;
            }
        },

        // 重置快速创建表单
        resetQuickCreateForm() {
            this.createCardStep = 0;
            this.selectedTemplate = null;
            this.quickCreateForm = {
                card_number: '',
                title: '',
                description: '',
                responsible_person: '',
                row_count: 5,
                create_date: new Date(),
                status: 'draft'
            };
            
            // 重置表单验证
            if (this.$refs.quickCreateForm) {
                this.$refs.quickCreateForm.resetFields();
            }
        },

        // 关闭流转卡详情对话框
        closeCardDetailDialog() {
            this.cardDetailDialogVisible = false;
            // 重置查看模式标志
            this.isViewMode = false;
            this.currentCardDetail = null;
        },

        // 监听菜单切换，重置快速创建表单
        handleMenuChange(newMenu) {
            if (newMenu !== 'create-card') {
                this.resetQuickCreateForm();
            }
        },

        // ========== 工作台页面相关方法 ==========

        // 计算属性：筛选后的操作记录
        filteredRecentOperations() {
            let filtered = this.recentOperations || [];
            
            // 按操作类型筛选
            if (this.operationFilter) {
                filtered = filtered.filter(op => op.action === this.operationFilter);
            }
            
            return filtered;
        },

        // 加载最近操作记录
        async loadRecentOperations() {
            this.loadingOperations = true;
            try {
                console.log(' 加载最近操作记录，页面:', this.currentPage);
                
                // 调用后端API获取操作记录
                const response = await TransferCardAPI.dashboard.getOperations({
                    page: this.currentPage,
                    per_page: 10
                });
                
                console.log('📡 操作记录API响应:', response);
                
                if (response.success) {
                    const operations = response.data.operations || [];
                    
                    // 合并新数据（分页加载）
                    if (this.currentPage === 1) {
                        this.recentOperations = operations;
                    } else {
                        this.recentOperations = [...this.recentOperations, ...operations];
                    }
                    
                    // 检查是否还有更多数据
                    this.hasMoreOperations = operations.length === 10 && 
                                          (response.data.total === undefined || 
                                           this.recentOperations.length < response.data.total);
                    
                    console.log(' 操作记录加载成功，当前数量:', this.recentOperations.length);
                } else {
                    console.error(' 操作记录API返回失败:', response.message);
                    this.$message.error(response.message || '加载操作记录失败');
                    
                    // 如果API失败，使用空数据
                    if (this.currentPage === 1) {
                        this.recentOperations = [];
                    }
                    this.hasMoreOperations = false;
                }
                
            } catch (error) {
                console.error(' 加载最近操作失败:', error);
                this.$message.error('加载操作记录失败，请检查网络连接');
                
                // 如果发生错误，清空数据
                if (this.currentPage === 1) {
                    this.recentOperations = [];
                }
                this.hasMoreOperations = false;
            } finally {
                this.loadingOperations = false;
            }
        },

        // 刷新最近操作
        refreshRecentOperations() {
            this.currentPage = 1;
            this.loadRecentOperations();
        },

        // 加载更多操作记录
        loadMoreOperations() {
            this.currentPage++;
            this.loadRecentOperations();
        },

        // 格式化操作时间
        formatOperationTime(timeStr) {
            if (!timeStr) return '';
            
            try {
                const now = new Date();
                const time = new Date(timeStr);
                const diff = now - time;
                
                // 小于1分钟
                if (diff < 1000 * 60) {
                    return '刚刚';
                }
                
                // 小于1小时
                if (diff < 1000 * 60 * 60) {
                    const minutes = Math.floor(diff / (1000 * 60));
                    return `${minutes}分钟前`;
                }
                
                // 小于1天
                if (diff < 1000 * 60 * 60 * 24) {
                    const hours = Math.floor(diff / (1000 * 60 * 60));
                    return `${hours}小时前`;
                }
                
                // 小于7天
                if (diff < 1000 * 60 * 60 * 24 * 7) {
                    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                    return `${days}天前`;
                }
                
                // 显示具体日期
                return time.toLocaleDateString('zh-CN');
                
            } catch (error) {
                return timeStr;
            }
        },

        // 获取用户头像
        getUserAvatar(userName) {
            // 使用简单的头像生成服务，实际应该使用用户头像
            return `https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=random&size=40`;
        },

        // 获取用户状态
        getUserStatus(userName) {
            // 模拟用户在线状态，实际应该根据用户活动时间判断
            const activeUsers = ['张三', '李四', '王五'];
            const busyUsers = ['赵六'];
            
            if (activeUsers.includes(userName)) {
                return 'online';
            } else if (busyUsers.includes(userName)) {
                return 'busy';
            } else {
                return 'offline';
            }
        },

        // 获取操作类型样式类
        getActionTypeClass(action) {
            return action || '';
        },

        // 获取部门标签类型
        getDepartmentTagType(departmentName) {
            const typeMap = {
                '研发部': 'primary',
                '采购部': 'success',
                '销售部': 'warning',
                '生产部': 'danger',
                '质检部': 'info',
                '仓库部': ''
            };
            return typeMap[departmentName] || '';
        },

        // 处理快捷操作
        handleQuickAction(action) {
            switch (action) {
                case 'create':
                    this.activeMenu = 'create-card';
                    break;
                case 'view':
                    this.activeMenu = 'cards';
                    break;
                case 'manage':
                    this.activeMenu = 'template-management';
                    break;
                case 'report':
                    this.$message.info('数据统计功能开发中...');
                    break;
            }
        },

        // ========== 实时数据更新方法 ==========

        // 启动实时数据更新
        startRealTimeUpdates() {
            // 清除现有定时器
            this.stopRealTimeUpdates();

            console.log(' 启动自动数据更新，间隔:', this.updateInterval / 1000, '秒');

            // 立即执行一次更新
            this.performRealTimeUpdate();

            // 设置定时更新
            this.realTimeUpdateTimer = setInterval(() => {
                this.performRealTimeUpdate();
            }, this.updateInterval);
        },

        // 停止实时数据更新
        stopRealTimeUpdates() {
            if (this.realTimeUpdateTimer) {
                clearInterval(this.realTimeUpdateTimer);
                this.realTimeUpdateTimer = null;
                console.log('⏹️ 停止实时数据更新');
            }
        },

        // 执行实时数据更新
        async performRealTimeUpdate() {
            if (!this.isLoggedIn || !this.currentUser) {
                return;
            }

            try {
                this.isUpdating = true;
                console.log(' 执行实时数据更新:', new Date().toLocaleTimeString());
                
                // 只在工作台页面更新统计数据
                if (this.activeMenu === 'dashboard') {
                    await this.updateDashboardStats();
                }
                
                // 在流转卡页面更新流转卡列表
                if (this.activeMenu === 'cards') {
                    await this.updateCardLists();
                }
                
                this.lastUpdateTime = new Date();
                
            } catch (error) {
                console.error(' 实时数据更新失败:', error);
                // 静默失败，不显示错误信息
            } finally {
                this.isUpdating = false;
            }
        },

        // 更新工作台统计数据
        async updateDashboardStats() {
            try {
                const response = await TransferCardAPI.dashboard.getStats();
                if (response.success) {
                    const oldData = { ...this.dashboardData };
                    this.dashboardData = response.data;
                    
                    // 检查数据是否有变化，如果有变化则显示提示
                    this.checkForDataChanges(oldData, this.dashboardData);
                    
                    console.log(' 工作台数据已更新:', this.dashboardData);
                }
            } catch (error) {
                console.error('更新工作台统计数据失败:', error);
            }
        },

        // 更新流转卡列表
        async updateCardLists() {
            try {
                // 同时更新普通流转卡和模板流转卡列表
                await Promise.all([
                    this.loadCards(),
                    this.loadTemplateCards()
                ]);
                console.log(' 流转卡列表已更新');
            } catch (error) {
                console.error('更新流转卡列表失败:', error);
            }
        },

        // 静默检测数据变化
        checkForDataChanges(oldData, newData) {
            let changeCount = 0;
            
            // 检查各项统计指标的变化
            if (oldData.pendingCards !== newData.pendingCards) changeCount++;
            if (oldData.totalCards !== newData.totalCards) changeCount++;
            if (oldData.completedToday !== newData.completedToday) changeCount++;
            if (oldData.weeklyTotal !== newData.weeklyTotal) changeCount++;
            
            // 静默记录变化，不显示UI提示
            if (changeCount > 0) {
                console.log(`📊 静默检测到 ${changeCount} 项数据变化`);
            }
        },

        // ========== 协作编辑方法 ==========

        // 初始化简化数据同步
        initializeDataSync() {
            try {
                console.log(' 初始化数据同步...');
                
                if (!window.simpleDataSync) {
                    console.warn(' 数据同步模块未找到，跳过初始化');
                    return;
                }
                
                // 设置数据同步回调
                window.simpleDataSync.on('onDataChange', (mergedData) => {
                    console.log(' 收到数据同步更新:', mergedData);
                    this.handleDataSyncChange(mergedData);
                });
                
                window.simpleDataSync.on('onSyncStart', () => {
                    this.syncStatus = 'running';
                });
                
                window.simpleDataSync.on('onSyncComplete', () => {
                    this.syncStatus = 'stopped';
                    this.lastSyncTime = new Date();
                });
                
                window.simpleDataSync.on('onError', (error) => {
                    console.error(' 数据同步错误:', error);
                    this.syncStatus = 'error';
                });
                
                console.log(' 数据同步初始化完成');
                
            } catch (error) {
                console.error(' 初始化数据同步失败:', error);
                this.$message.error('数据同步功能初始化失败');
            }
        },

        // 加入流转卡协作编辑
        async joinCardCollaboration(cardId) {
            try {
                if (!this.collaborationClient || !this.currentUser) {
                    this.$message.warning('协作功能未可用');
                    return false;
                }
                
                console.log(' 加入流转卡协作:', cardId);
                this.collaborationStatus = 'connecting';
                this.currentEditingCardId = cardId;
                
                const result = await this.collaborationClient.joinCard(cardId, {
                    userId: this.currentUser.id,
                    userName: this.currentUser.real_name || this.currentUser.username,
                    department: this.currentUser.department_name,
                    role: this.currentUser.role
                });
                
                if (result.success) {
                    this.isCollaborationEnabled = true;
                    this.activeUsers = result.activeUsers || [];
                    console.log(' 成功加入协作编辑');
                    return true;
                } else {
                    this.$message.error(result.message || '加入协作失败');
                    return false;
                }
                
            } catch (error) {
                console.error(' 加入协作编辑失败:', error);
                this.$message.error('加入协作编辑失败');
                return false;
            }
        },

        // 离开流转卡协作编辑
        leaveCardCollaboration() {
            try {
                if (!this.collaborationClient) {
                    return;
                }
                
                console.log(' 离开流转卡协作:', this.currentEditingCardId);
                
                this.collaborationClient.leaveCard(this.currentEditingCardId);
                this.isCollaborationEnabled = false;
                this.currentEditingCardId = null;
                this.activeUsers = [];
                this.stopAutoSave();
                
                console.log(' 已离开协作编辑');
                
            } catch (error) {
                console.error(' 离开协作编辑失败:', error);
            }
        },

        // 处理协作数据变化
        handleCollaborationDataChange(data) {
            try {
                console.log(' 处理协作数据变化:', data);
                
                if (!this.currentEditingCardId || data.cardId !== this.currentEditingCardId) {
                    return;
                }
                
                // 更新本地数据
                if (data.type === 'cell_change') {
                    this.updateCellData(data.rowIndex, data.fieldName, data.value, data.userId);
                } else if (data.type === 'row_add') {
                    this.addRemoteRow(data.rowData, data.rowIndex);
                } else if (data.type === 'row_delete') {
                    this.deleteRemoteRow(data.rowIndex);
                } else if (data.type === 'full_sync') {
                    this.handleFullSync(data.data);
                }
                
                this.lastSyncTime = new Date();
                
            } catch (error) {
                console.error(' 处理协作数据变化失败:', error);
            }
        },

        // 更新单元格数据
        updateCellData(rowIndex, fieldName, value, remoteUserId) {
            try {
                // 如果是其他用户的更改，更新本地数据但不触发广播
                if (remoteUserId !== this.currentUser.id) {
                    if (this.cardDataTable && this.cardDataTable[rowIndex]) {
                        this.$set(this.cardDataTable[rowIndex], fieldName, value);
                        
                        // 显示用户正在编辑的指示器
                        this.showEditIndicator(rowIndex, fieldName, remoteUserId);
                    }
                }
                
            } catch (error) {
                console.error(' 更新单元格数据失败:', error);
            }
        },

        // 添加远程行
        addRemoteRow(rowData, rowIndex) {
            try {
                if (this.cardDataTable) {
                    this.cardDataTable.splice(rowIndex, 0, rowData);
                    this.$message.info('其他用户添加了新行');
                }
            } catch (error) {
                console.error(' 添加远程行失败:', error);
            }
        },

        // 删除远程行
        deleteRemoteRow(rowIndex) {
            try {
                if (this.cardDataTable && this.cardDataTable.length > 1) {
                    this.cardDataTable.splice(rowIndex, 1);
                    this.$message.info('其他用户删除了一行');
                }
            } catch (error) {
                console.error(' 删除远程行失败:', error);
            }
        },

        // 处理完整同步
        handleFullSync(serverData) {
            try {
                console.log(' 执行完整数据同步');
                this.cardDataTable = serverData;
                this.$message.success('数据已同步到最新状态');
            } catch (error) {
                console.error(' 完整同步失败:', error);
            }
        },

        // 显示编辑指示器
        showEditIndicator(rowIndex, fieldName, userId) {
            // 这里可以添加视觉指示器，显示哪个用户正在编辑哪个单元格
            const user = this.activeUsers.find(u => u.id === userId);
            if (user) {
                console.log(`👤 ${user.name} 正在编辑第${rowIndex + 1}行 ${fieldName} 字段`);
            }
        },

        // 处理协作冲突
        handleCollaborationConflict(conflict) {
            try {
                console.log(' 处理协作冲突:', conflict);
                
                // 显示冲突解决对话框
                this.$confirm(`检测到数据冲突：${conflict.message}`, '协作冲突', {
                    confirmButtonText: '使用我的数据',
                    cancelButtonText: '使用服务器数据',
                    type: 'warning'
                }).then(() => {
                    // 用户选择保留自己的数据
                    this.resolveConflict(conflict.id, 'local');
                }).catch(() => {
                    // 用户选择使用服务器数据
                    this.resolveConflict(conflict.id, 'server');
                });
                
            } catch (error) {
                console.error(' 处理协作冲突失败:', error);
            }
        },

        // 解决冲突
        resolveConflict(conflictId, resolution) {
            try {
                if (!this.collaborationClient) {
                    return;
                }
                
                this.collaborationClient.resolveConflict(conflictId, resolution);
                this.conflictResolution = null;
                
            } catch (error) {
                console.error(' 解决冲突失败:', error);
            }
        },

        // 广播数据变化
        broadcastDataChange(type, data) {
            try {
                if (!this.collaborationClient || !this.isCollaborationEnabled) {
                    return;
                }
                
                this.collaborationClient.broadcastChange({
                    type: type,
                    cardId: this.currentEditingCardId,
                    userId: this.currentUser.id,
                    data: data
                });
                
            } catch (error) {
                console.error(' 广播数据变化失败:', error);
            }
        },

        // 启动自动保存
        startAutoSave() {
            try {
                this.stopAutoSave();
                
                this.autoSaveTimer = setInterval(() => {
                    this.autoSave();
                }, 5000); // 每5秒自动保存
                
                console.log(' 自动保存已启动');
                
            } catch (error) {
                console.error(' 启动自动保存失败:', error);
            }
        },

        // 停止自动保存
        stopAutoSave() {
            if (this.autoSaveTimer) {
                clearInterval(this.autoSaveTimer);
                this.autoSaveTimer = null;
                console.log('⏹️ 自动保存已停止');
            }
        },

        // 自动保存
        async autoSave() {
            try {
                if (!this.isCollaborationEnabled || !this.currentEditingCardId) {
                    return;
                }
                
                // 检查是否有待保存的更改
                if (Object.keys(this.pendingChanges).length === 0) {
                    return;
                }
                
                console.log('💾 执行自动保存');
                
                // 这里调用保存API
                await this.saveCardData();
                
                // 清空待保存的更改
                this.pendingChanges = {};
                
            } catch (error) {
                console.error(' 自动保存失败:', error);
            }
        },

        // 修改后的保存流转卡数据方法（带协作功能）
        async saveCardDataWithCollaboration() {
            try {
                if (!this.currentCardDetail || !this.currentCardDetail.id) {
                    this.$message.error('流转卡信息不完整');
                    return;
                }

                // 如果启用了协作，先广播变化
                if (this.isCollaborationEnabled) {
                    this.broadcastDataChange('full_sync', {
                        table_data: this.cardDataTable
                    });
                }

                // 直接使用cardDataTable，不再需要过滤部门行
                const updateData = {
                    table_data: this.cardDataTable
                };

                const response = await TransferCardAPI.card.updateCardData(this.currentCardDetail.id, updateData);
                
                if (response.success) {
                    this.$message.success('数据保存成功');
                    
                    // 如果启用了协作，通知其他用户数据已保存
                    if (this.isCollaborationEnabled) {
                        this.broadcastDataChange('save_complete', {
                            timestamp: new Date().toISOString()
                        });
                    }
                    
                    // 重新加载数据
                    await this.loadCardDetailData(this.currentCardDetail.id);
                } else {
                    this.$message.error(response.message || '保存失败');
                }
            } catch (error) {
                console.error('保存流转卡数据失败:', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 修改后的流转卡详情查看方法（带协作功能）
        async viewCardDetailWithCollaboration(card) {
            try {
                this.currentCardDetail = { ...card };
                this.cardDetailDialogVisible = true;
                
                // 设置查看模式标志
                this.isViewMode = true;
                
                // 加载流转卡详细数据
                await this.loadCardDetailData(card.id);
                
                // 尝试加入协作编辑
                if (this.canEditCard(card)) {
                    await this.joinCardCollaboration(card.id);
                }
                
            } catch (error) {
                console.error('加载流转卡详情失败:', error);
                this.$message.error('加载流转卡详情失败');
            }
        },

        // 修改后的流转卡编辑方法（带数据同步）
        async editCardDataWithCollaboration(card) {
            try {
                this.currentEditingCard = { ...card };
                this.cardDataEditForm = {
                    status: card.status,
                    table_data: []
                };
                
                // 加载流转卡字段和数据
                await this.loadCardEditData(card.id);
                
                // 启用数据同步
                this.enableDataSync(card.id);
                
                this.cardDataEditDialogVisible = true;
                
            } catch (error) {
                console.error('加载编辑数据失败:', error);
                this.$message.error('加载编辑数据失败');
            }
        },

        // 关闭对话框时清理协作状态
        closeCardDetailDialogWithCleanup() {
            this.leaveCardCollaboration();
            this.cardDetailDialogVisible = false;
            this.isViewMode = false;
            this.currentCardDetail = null;
        },

        closeCardDataEditDialogWithCleanup() {
            this.leaveCardCollaboration();
            this.cleanupCollaborativeEdit();
            this.cardDataEditDialogVisible = false;
            this.currentEditingCard = null;
        },

        // 初始化新的协作编辑方案
        initCollaborativeEdit(cardId) {
            try {
                console.log(' 初始化协作编辑方案v2.0，ID:', cardId);
                
                if (!window.collaborativeEditV2) {
                    console.warn(' 协作编辑v2.0模块未找到');
                    return;
                }
                
                const token = TransferCardAPI.getAuthToken();
                if (!token) {
                    console.error(' 未找到认证token');
                    return;
                }
                
                // 设置Vue实例引用
                window.collaborativeEditV2.setVueInstance(this);
                
                // 初始化协作编辑
                window.collaborativeEditV2.init(
                    cardId,
                    {
                        status: this.cardDataEditForm.status,
                        table_data: this.cardDataEditForm.table_data
                    },
                    token
                );
                
                // 设置事件回调
                window.collaborativeEditV2.on('onSaveComplete', (result) => {
                    console.log(' 协作编辑保存完成:', result);
                    this.$message.success('数据保存成功');
                    this.cardDataEditDialogVisible = false;
                    this.loadTemplateCards(); // 刷新列表
                });
                
                window.collaborativeEditV2.on('onError', (error) => {
                    console.error(' 协作编辑错误:', error);
                    this.$message.error(error.message || '保存失败');
                });
                
                console.log(' 协作编辑v2.0初始化完成');
                
            } catch (error) {
                console.error(' 初始化协作编辑失败:', error);
                this.$message.error('协作编辑功能初始化失败');
            }
        },

        // 清理协作编辑状态
        cleanupCollaborativeEdit() {
            try {
                if (window.collaborativeEditV2) {
                    window.collaborativeEditV2.destroy();
                }
                console.log(' 协作编辑状态已清理');
            } catch (error) {
                console.error(' 清理协作编辑状态失败:', error);
            }
        },

        // 使用新的协作编辑方案保存数据
        async saveCardDataEditWithCollaborativeEdit() {
            try {
                if (!this.currentEditingCard || !this.currentEditingCard.id) {
                    this.$message.error('流转卡信息不完整');
                    return;
                }

                const saveData = {
                    status: this.cardDataEditForm.status,
                    table_data: this.cardDataEditForm.table_data
                };

                console.log('💾 使用协作编辑v2.0保存数据');
                
                // 检查协作编辑模块是否存在
                if (window.collaborativeEditV2) {
                    // 使用协作编辑保存
                    const result = await window.collaborativeEditV2.save(saveData);
                    if (result.success) {
                        this.$message.success('数据保存成功');
                        this.cardDataEditDialogVisible = false;
                        this.loadTemplateCards(); // 刷新列表
                    } else {
                        this.$message.error(result.message || '保存失败');
                    }
                } else {
                    // 回退到普通保存方法
                    console.log(' 协作编辑模块不可用，使用普通保存');
                    const response = await TransferCardAPI.card.updateCardData(this.currentEditingCard.id, saveData);
                    
                    if (response.success) {
                        this.$message.success('数据保存成功');
                        this.cardDataEditDialogVisible = false;
                        this.loadTemplateCards(); // 刷新列表
                    } else {
                        this.$message.error(response.message || '保存失败');
                    }
                }
                
            } catch (error) {
                console.error(' 保存流转卡数据失败:', error);
                this.$message.error('保存失败，请检查网络连接');
            }
        },

        // 获取协作状态文本
        getCollaborationStatusText() {
            const statusMap = {
                'disconnected': '未连接',
                'connecting': '连接中',
                'connected': '已连接',
                'syncing': '同步中'
            };
            return statusMap[this.collaborationStatus] || '未知状态';
        },

        // 获取协作状态类型
        getCollaborationStatusType() {
            const typeMap = {
                'disconnected': 'danger',
                'connecting': 'warning',
                'connected': 'success',
                'syncing': 'primary'
            };
            return typeMap[this.collaborationStatus] || 'info';
        },

        // ========== 协作编辑事件处理方法 ==========

        // 处理单元格变化
        onCellChange(rowIndex, fieldName, value, field) {
            try {
                // 如果没有启用协作，直接返回
                if (!this.isCollaborationEnabled) {
                    return;
                }

                // 防抖处理，避免频繁发送
                if (this.cellChangeTimeout) {
                    clearTimeout(this.cellChangeTimeout);
                }

                this.cellChangeTimeout = setTimeout(() => {
                    console.log(' 单元格变化:', { rowIndex, fieldName, value, field });
                    
                    // 记录待保存的更改
                    this.$set(this.pendingChanges, `${rowIndex}-${fieldName}`, {
                        value: value,
                        field: field,
                        timestamp: new Date().toISOString()
                    });

                    // 广播单元格变化到其他用户
                    this.broadcastDataChange('cell_change', {
                        rowIndex: rowIndex,
                        fieldName: fieldName,
                        value: value,
                        fieldType: field.field_type,
                        userId: this.currentUser.id
                    });
                }, 300); // 300ms防抖

            } catch (error) {
                console.error(' 处理单元格变化失败:', error);
            }
        },

        // 处理单元格获得焦点
        onCellFocus(rowIndex, fieldName) {
            try {
                if (!this.isCollaborationEnabled) {
                    return;
                }

                console.log('🎯 单元格获得焦点:', { rowIndex, fieldName });
                
                // 广播焦点事件，显示哪个用户正在编辑
                this.broadcastDataChange('cell_focus', {
                    rowIndex: rowIndex,
                    fieldName: fieldName,
                    userId: this.currentUser.id
                });

            } catch (error) {
                console.error(' 处理单元格焦点失败:', error);
            }
        },

        // 处理单元格失去焦点
        onCellBlur(rowIndex, fieldName) {
            try {
                if (!this.isCollaborationEnabled) {
                    return;
                }

                console.log('📤 单元格失去焦点:', { rowIndex, fieldName });
                
                // 广播失去焦点事件
                this.broadcastDataChange('cell_blur', {
                    rowIndex: rowIndex,
                    fieldName: fieldName,
                    userId: this.currentUser.id
                });

            } catch (error) {
                console.error(' 处理单元格失焦失败:', error);
            }
        },

        // ========== 数据同步相关方法 ==========

        // 启用数据同步
        enableDataSync(cardId) {
            try {
                console.log(' 启用数据同步，流转卡ID:', cardId);
                
                if (!window.simpleDataSync) {
                    console.warn(' 数据同步模块未可用');
                    return false;
                }
                
                const token = TransferCardAPI.getAuthToken();
                if (!token) {
                    console.error(' 未找到认证token');
                    return false;
                }
                
                this.currentEditingCardId = cardId;
                this.dataSyncEnabled = true;
                
                // 初始化数据同步
                window.simpleDataSync.init(cardId, token);
                
                // 设置当前数据
                window.simpleDataSync.setCurrentData({
                    table_data: this.cardDataEditForm.table_data
                });
                
                console.log(' 数据同步已启用');
                return true;
                
            } catch (error) {
                console.error(' 启用数据同步失败:', error);
                this.$message.error('启用数据同步失败');
                return false;
            }
        },

        // 启用数据同步（流转卡版本）
        enableDataSyncForCard(cardId) {
            try {
                console.log(' 启用流转卡数据同步，ID:', cardId);
                
                if (!window.simpleDataSync) {
                    console.warn(' 数据同步模块未可用');
                    return false;
                }
                
                const token = TransferCardAPI.getAuthToken();
                if (!token) {
                    console.error(' 未找到认证token');
                    return false;
                }
                
                this.currentEditingCardId = cardId;
                this.dataSyncEnabled = true;
                
                // 初始化数据同步
                window.simpleDataSync.init(cardId, token);
                
                // 设置当前数据
                window.simpleDataSync.setCurrentData({
                    table_data: this.cardDataEditForm.table_data
                });
                
                console.log(' 流转卡数据同步已启用');
                return true;
                
            } catch (error) {
                console.error(' 启用流转卡数据同步失败:', error);
                this.$message.error('启用数据同步失败');
                return false;
            }
        },

        // 禁用数据同步
        disableDataSync() {
            try {
                if (window.simpleDataSync) {
                    window.simpleDataSync.destroy();
                }
                
                this.dataSyncEnabled = false;
                this.currentEditingCardId = null;
                console.log(' 数据同步已禁用');
                
            } catch (error) {
                console.error(' 禁用数据同步失败:', error);
            }
        },

        // 处理数据同步变化（重新设计：真正实现数据同步）
        handleDataSyncChange(mergedData) {
            try {
                console.log(' ===== 开始处理数据同步变化 =====');
                console.log('📊 服务器合并数据:', mergedData);
                console.log('📊 对话框状态:', this.cardDataEditDialogVisible);
                
                if (!this.cardDataEditDialogVisible || !mergedData.table_data) {
                    console.log(' 对话框未打开或无数据，跳过同步');
                    return;
                }
                
                // 捕获当前用户正在编辑的内容
                const currentUserEdits = this.captureCurrentUserEdits();
                console.log('📸 捕获到当前用户编辑:', currentUserEdits);
                
                // 智能合并：服务器数据 + 当前用户编辑
                const finalData = this.mergeServerAndUserData(mergedData, currentUserEdits);
                console.log('🧠 智能合并后的最终数据:', finalData);
                
                // 更新Vue数据（这会更新DOM）
                this.cardDataEditForm.table_data = finalData;
                
                // 在Vue更新完成后，恢复用户正在编辑的内容
                this.$nextTick(() => {
                    this.$nextTick(() => {
                        this.restoreUserEdits(currentUserEdits);
                        console.log(' 数据同步完成，用户编辑已恢复');
                        
                        // 显示友好的同步消息
                        const hasServerChanges = this.detectServerChanges(mergedData);
                        const hasUserEdits = currentUserEdits.size > 0;
                        
                        if (hasServerChanges && hasUserEdits) {
                            this.$message({
                                message: '检测到其他用户更新，您的编辑内容已保留',
                                type: 'success',
                                duration: 3000,
                                showClose: true
                            });
                        } else if (hasServerChanges) {
                            this.$message({
                                message: '数据已同步到最新版本',
                                type: 'info',
                                duration: 2000,
                                showClose: true
                            });
                        }
                    });
                });
                
            } catch (error) {
                console.error(' 处理数据同步变化失败:', error);
                this.$message.error('数据同步处理失败，请刷新页面');
            }
        },

        // 捕获当前编辑状态（从DOM输入框获取）
        captureCurrentEditingStates() {
            const editingStates = new Map();
            
            try {
                // 查找所有可见的输入框
                const inputs = document.querySelectorAll('input[el-input__inner], textarea');
                
                inputs.forEach(input => {
                    // 获取行号和字段名（从input的data属性或从父元素解析）
                    const rowNumber = this.getRowNumberFromInput(input);
                    const fieldName = this.getFieldNameFromInput(input);
                    
                    if (rowNumber && fieldName && input.value.trim() !== '') {
                        if (!editingStates.has(rowNumber)) {
                            editingStates.set(rowNumber, {});
                        }
                        editingStates.get(rowNumber)[fieldName] = input.value;
                        console.log(` 捕获编辑状态: 行${rowNumber} 字段${fieldName} = ${input.value}`);
                    }
                });
                
                // 同时从数据同步模块获取待保存的更改
                if (window.simpleDataSync && window.simpleDataSync.pendingChanges) {
                    window.simpleDataSync.pendingChanges.forEach((change, rowNumber) => {
                        if (!editingStates.has(rowNumber)) {
                            editingStates.set(rowNumber, {});
                        }
                        Object.assign(editingStates.get(rowNumber), change.values);
                        console.log(` 从同步模块获取: 行${rowNumber}`, change.values);
                    });
                }
                
            } catch (error) {
                console.error(' 捕获编辑状态失败:', error);
            }
            
            return editingStates;
        },

        // 恢复编辑状态到输入框
        restoreEditingStates(editingStates) {
            try {
                editingStates.forEach((fields, rowNumber) => {
                    Object.entries(fields).forEach(([fieldName, value]) => {
                        // 查找对应的输入框
                        const input = this.findInputForRowAndField(rowNumber, fieldName);
                        if (input && input.value !== value) {
                            input.value = value;
                            console.log(` 恢复编辑状态: 行${rowNumber} 字段${fieldName} = ${value}`);
                            
                            // 触发input事件以确保Vue响应式更新
                            const event = new Event('input', { bubbles: true });
                            input.dispatchEvent(event);
                        }
                    });
                });
            } catch (error) {
                console.error(' 恢复编辑状态失败:', error);
            }
        },

        // 从输入框获取行号
        getRowNumberFromInput(input) {
            try {
                // 尝试多种方式获取行号
                const rowElement = input.closest('tr');
                if (rowElement) {
                    const rowIndex = Array.from(rowElement.parentNode.children).indexOf(rowElement);
                    return rowIndex + 1; // 行号从1开始
                }
                
                // 从data属性获取
                const rowNum = input.getAttribute('data-row-number') || 
                               input.closest('[data-row-number]')?.getAttribute('data-row-number');
                return rowNum ? parseInt(rowNum) : null;
            } catch (error) {
                return null;
            }
        },

        // 从输入框获取字段名
        getFieldNameFromInput(input) {
            try {
                // 从data属性获取
                const fieldName = input.getAttribute('data-field-name') || 
                                 input.closest('[data-field-name]')?.getAttribute('data-field-name');
                
                if (fieldName) return fieldName;
                
                // 从name属性获取
                if (input.name) return input.name;
                
                // 从占位符或父元素解析
                const parent = input.closest('td');
                if (parent) {
                    const headerCell = parent.closest('table')?.querySelector('th')?.textContent;
                    return headerCell?.trim() || null;
                }
                
                return null;
            } catch (error) {
                return null;
            }
        },

        // 查找指定行和字段的输入框
        findInputForRowAndField(rowNumber, fieldName) {
            try {
                // 查找指定行的输入框
                const rowElement = document.querySelector(`tr:nth-child(${rowNumber})`);
                if (!rowElement) return null;
                
                // 在行内查找指定字段的输入框
                const input = rowElement.querySelector(`[data-field-name="${fieldName}"]`) ||
                             rowElement.querySelector(`[name="${fieldName}"]`) ||
                             rowElement.querySelector('input') ||
                             rowElement.querySelector('textarea');
                
                return input;
            } catch (error) {
                return null;
            }
        },

        // 处理单元格编辑开始（数据同步版）
        onCellEditStart(rowNumber, fieldName, value) {
            try {
                if (!this.dataSyncEnabled || !window.simpleDataSync) {
                    return;
                }
                
                console.log('✏️ 开始编辑单元格:', { rowNumber, fieldName, value });
                
                // 通知数据同步模块用户开始编辑
                window.simpleDataSync.startEditing(rowNumber, fieldName, value);
                
            } catch (error) {
                console.error(' 处理单元格编辑开始失败:', error);
            }
        },

        // 处理单元格编辑结束（数据同步版）
        onCellEditEnd(rowNumber) {
            try {
                if (!this.dataSyncEnabled || !window.simpleDataSync) {
                    return;
                }
                
                console.log(' 结束编辑单元格:', rowNumber);
                
                // 通知数据同步模块用户结束编辑
                window.simpleDataSync.stopEditing(rowNumber);
                
            } catch (error) {
                console.error(' 处理单元格编辑结束失败:', error);
            }
        },

        // 清理数据同步状态
        cleanupDataSync() {
            try {
                this.disableDataSync();
                
                // 清理相关数据
                this.pendingChanges = {};
                this.otherUsersData.clear();
                
                console.log(' 数据同步状态已清理');
                
            } catch (error) {
                console.error(' 清理数据同步状态失败:', error);
            }
        },

        // 获取数据同步状态文本
        getSyncStatusText() {
            const statusMap = {
                'stopped': '已停止',
                'running': '同步中',
                'error': '同步错误'
            };
            return statusMap[this.syncStatus] || '未知状态';
        },

        // 获取数据同步状态类型
        getSyncStatusType() {
            const typeMap = {
                'stopped': 'info',
                'running': 'success',
                'error': 'danger'
            };
            return typeMap[this.syncStatus] || 'info';
        },

        // 捕获DOM中的输入框状态
        captureDOMInputs() {
            const domInputs = new Map();
            
            try {
                console.log(' 开始捕获DOM输入框状态');
                
                // 查找所有输入框，包括Element UI的输入框
                const inputs = document.querySelectorAll(
                    'input.el-input__inner, input[type="text"], textarea, ' +
                    'input.el-date-editor, input.el-number__input'
                );
                
                console.log(` 找到 ${inputs.length} 个输入框`);
                
                inputs.forEach((input, index) => {
                    try {
                        // 获取行号
                        const rowElement = input.closest('tr');
                        if (!rowElement) return;
                        
                        const rowNumber = Array.from(rowElement.parentNode.children).indexOf(rowElement) + 1;
                        if (!rowNumber || rowNumber < 1) return;
                        
                        // 获取字段名
                        const fieldName = this.getFieldNameFromInput(input);
                        if (!fieldName) return;
                        
                        // 获取当前值
                        const currentValue = input.value || '';
                        
                        // 只记录非空的或有意义的输入
                        if (currentValue.trim() !== '') {
                            if (!domInputs.has(rowNumber)) {
                                domInputs.set(rowNumber, {});
                            }
                            domInputs.get(rowNumber)[fieldName] = currentValue;
                            
                            console.log(` DOM输入框捕获: 行${rowNumber} 字段${fieldName} = "${currentValue}"`);
                        }
                        
                    } catch (error) {
                        console.error(` 捕获输入框${index}失败:`, error);
                    }
                });
                
                console.log(' DOM输入框捕获完成，保护行数:', domInputs.size);
                
            } catch (error) {
                console.error(' 捕获DOM输入失败:', error);
            }
            
            return domInputs;
        },

        // 恢复DOM输入框状态（增强版：强制保持用户输入）
        restoreDOMInputs(domInputs) {
            try {
                console.log(' 开始恢复DOM输入框状态，行数:', domInputs.size);
                
                // 使用更强力的方法保护用户输入
                const protectUserInput = (input, value, rowNumber, fieldName) => {
                    if (!input || input.value === value) return;
                    
                    console.log(` 强制恢复用户输入: 行${rowNumber} 字段${fieldName} = "${value}"`);
                    
                    // 方法1：直接设置value属性
                    input.value = value;
                    
                    // 方法2：设置defaultValue（防止被Vue重置）
                    input.defaultValue = value;
                    
                    // 方法3：设置setAttribute
                    input.setAttribute('value', value);
                    
                    // 方法4：阻止Vue的响应式更新
                    input._vueIgnore = true;
                    
                    // 方法5：触发多个事件确保Vue状态同步
                    const events = ['input', 'change', 'blur', 'focus'];
                    events.forEach(eventType => {
                        const event = new Event(eventType, { 
                            bubbles: true, 
                            cancelable: true 
                        });
                        input.dispatchEvent(event);
                    });
                    
                    // 方法6：延迟再次设置（防止异步覆盖）
                    setTimeout(() => {
                        input.value = value;
                        input.setAttribute('value', value);
                    }, 10);
                };
                
                domInputs.forEach((fields, rowNumber) => {
                    Object.entries(fields).forEach(([fieldName, value]) => {
                        // 查找对应的输入框
                        const input = this.findInputForRowAndField(rowNumber, fieldName);
                        if (input && input.value !== value) {
                            protectUserInput(input, value, rowNumber, fieldName);
                        }
                    });
                });
                
                // 方法7：全局定时器，持续保护用户输入
                if (this.domProtectionTimer) {
                    clearInterval(this.domProtectionTimer);
                }
                
                this.domProtectionTimer = setInterval(() => {
                    domInputs.forEach((fields, rowNumber) => {
                        Object.entries(fields).forEach(([fieldName, value]) => {
                            const input = this.findInputForRowAndField(rowNumber, fieldName);
                            if (input && input.value !== value) {
                                protectUserInput(input, value, rowNumber, fieldName);
                            }
                        });
                    });
                }, 100); // 每100ms检查一次
                
                console.log(' DOM输入框状态恢复完成，启动持续保护');
                
            } catch (error) {
                console.error(' 恢复DOM输入失败:', error);
            }
        },

        // 查找指定行和字段的输入框（改进版）
        findInputForRowAndField(rowNumber, fieldName) {
            try {
                // 查找指定行
                const rowElement = document.querySelector(`tr:nth-child(${rowNumber})`);
                if (!rowElement) {
                    console.warn(` 未找到行${rowNumber}`);
                    return null;
                }
                
                // 在行内查找输入框的多种方式
                let input = null;
                
                // 方式1：通过data属性查找
                input = rowElement.querySelector(`[data-field-name="${fieldName}"]`) ||
                       rowElement.querySelector(`[name="${fieldName}"]`);
                
                if (input) return input;
                
                // 方式2：通过表头文本查找字段对应的列
                const table = rowElement.closest('table');
                if (table) {
                    const headers = table.querySelectorAll('th');
                    let columnIndex = -1;
                    
                    headers.forEach((header, index) => {
                        const headerText = header.textContent.trim();
                        if (headerText === fieldName || headerText.includes(fieldName)) {
                            columnIndex = index;
                        }
                    });
                    
                    if (columnIndex >= 0) {
                        const cells = rowElement.querySelectorAll('td');
                        if (cells[columnIndex]) {
                            input = cells[columnIndex].querySelector('input') ||
                                   cells[columnIndex].querySelector('textarea');
                        }
                    }
                }
                
                // 方式3：查找第一个输入框（如果字段名不明确）
                if (!input) {
                    input = rowElement.querySelector('input') ||
                           rowElement.querySelector('textarea');
                }
                
                return input;
                
            } catch (error) {
                console.error(` 查找输入框失败 行${rowNumber} 字段${fieldName}:`, error);
                return null;
            }
        },

        // ========== 部门流转顺序设置方法 ==========

        // 打开流转设置对话框
        async openFlowSettings(template) {
            try {
                this.flowSettingsTemplate = { ...template };
                
                // 加载可用部门
                await this.loadAvailableDepartments();
                
                // 加载模板的流转部门
                await this.loadTemplateFlowDepartments(template.id);
                
                this.flowSettingsDialogVisible = true;
            } catch (error) {
                console.error('打开流转设置失败:', error);
                this.$message.error('打开流转设置失败');
            }
        },

        // 加载可用部门
        async loadAvailableDepartments() {
            try {
                const response = await TransferCardAPI.user.getDepartments();
                if (response.success) {
                    this.availableDepartmentsForFlow = response.data || [];
                }
            } catch (error) {
                console.error('加载部门列表失败:', error);
                this.$message.error('加载部门列表失败');
            }
        },

        // 加载模板的流转部门
        async loadTemplateFlowDepartments(templateId) {
            try {
                const response = await axios.get(
                    `http://localhost:5000/api/flow/templates/${templateId}/departments`,
                    {
                        headers: {
                            'Authorization': `Bearer ${TransferCardAPI.getAuthToken()}`
                        }
                    }
                );
                
                if (response.data.success) {
                    this.templateFlowDepartments = response.data.data || [];
                } else {
                    this.$message.error(response.data.message || '加载流转部门失败');
                }
            } catch (error) {
                console.error('加载流转部门失败:', error);
                this.$message.error('加载流转部门失败，请检查网络连接');
            }
        },

        // 添加部门到流转顺序
        addDepartmentToFlow() {
            if (!this.newDepartmentForFlow) {
                this.$message.warning('请选择要添加的部门');
                return;
            }

            // 检查部门是否已经在流转顺序中
            const exists = this.templateFlowDepartments.some(
                dept => dept.department_id === this.newDepartmentForFlow
            );

            if (exists) {
                this.$message.warning('该部门已在流转顺序中');
                return;
            }

            // 添加到流转顺序末尾
            const nextOrder = this.templateFlowDepartments.length + 1;
            const newDept = {
                department_id: this.newDepartmentForFlow,
                flow_order: nextOrder,
                is_required: true,
                auto_skip: false,
                timeout_hours: 24
            };

            this.templateFlowDepartments.push(newDept);
            this.newDepartmentForFlow = null;
        },

        // 删除流转部门
        removeDepartmentFromFlow(dept) {
            const index = this.templateFlowDepartments.indexOf(dept);
            if (index > -1) {
                this.templateFlowDepartments.splice(index, 1);
                // 重新排序
                this.reorderFlowDepartments();
            }
        },

        // 上移流转部门
        moveDepartmentUp(dept) {
            const index = this.templateFlowDepartments.indexOf(dept);
            if (index > 0) {
                this.templateFlowDepartments.splice(index, 1);
                this.templateFlowDepartments.splice(index - 1, 0, dept);
                this.reorderFlowDepartments();
            }
        },

        // 下移流转部门
        moveDepartmentDown(dept) {
            const index = this.templateFlowDepartments.indexOf(dept);
            if (index < this.templateFlowDepartments.length - 1) {
                this.templateFlowDepartments.splice(index, 1);
                this.templateFlowDepartments.splice(index + 1, 0, dept);
                this.reorderFlowDepartments();
            }
        },

        // 重新排序流转部门
        reorderFlowDepartments() {
            this.templateFlowDepartments.forEach((dept, index) => {
                dept.flow_order = index + 1;
            });
        },

        // 保存流转顺序设置
        async saveFlowSettings() {
            try {
                if (this.templateFlowDepartments.length === 0) {
                    this.$message.warning('请至少添加一个流转部门');
                    return;
                }

                const response = await axios.post(
                    `http://localhost:5000/api/flow/templates/${this.flowSettingsTemplate.id}/departments`,
                    { departments: this.templateFlowDepartments },
                    {
                        headers: {
                            'Authorization': `Bearer ${TransferCardAPI.getAuthToken()}`,
                            'Content-Type': 'application/json'
                        }
                    }
                );

                if (response.data.success) {
                    this.$message.success('流转顺序设置成功');
                    this.flowSettingsDialogVisible = false;
                } else {
                    this.$message.error(response.data.message || '保存失败');
                }
            } catch (error) {
                console.error('保存流转顺序失败:', error);
                this.$message.error('保存流转顺序失败，请检查网络连接');
            }
        },

        // 取消流转设置
        cancelFlowSettings() {
            this.flowSettingsDialogVisible = false;
            this.templateFlowDepartments = [];
            this.flowSettingsTemplate = {};
        },

        // 根据部门ID获取部门名称
        getDepartmentName(departmentId) {
            if (!departmentId || !this.availableDepartmentsForFlow) {
                return '';
            }
            
            const department = this.availableDepartmentsForFlow.find(
                dept => dept.id === departmentId
            );
            
            return department ? department.name : '';
        },

        // ========== 流转卡流转提交方法 ==========

        // 检查是否可以提交到下一部门
        canSubmitToNextDepartment() {
            if (!this.currentEditingCard) {
                return false;
            }

            // 管理员始终可以提交
            if (this.currentUser && this.currentUser.role === 'admin') {
                return true;
            }

            // 检查流转卡状态
            if (this.currentEditingCard.status === 'completed' || 
                this.currentEditingCard.status === 'cancelled') {
                return false;
            }

            // 检查当前部门是否匹配
            if (this.currentEditingCard.current_department_name !== this.currentUser.department_name) {
                return false;
            }

            // 检查是否有流转配置
            if (!this.currentEditingCard.flow_departments || this.currentEditingCard.flow_departments.length === 0) {
                return false;
            }

            return true;
        },

        // 提交流转卡到下一部门
        async submitCardToNextDepartment() {
            try {
                if (!this.currentEditingCard || !this.currentEditingCard.id) {
                    this.$message.error('流转卡信息不完整');
                    return;
                }

                // 确认提交
                const confirmMessage = '确定要将此流转卡提交到下一部门吗？\n提交后，当前部门的填写将被锁定。';
                await this.$confirm(confirmMessage, '确认提交', {
                    confirmButtonText: '确定提交',
                    cancelButtonText: '取消',
                    type: 'warning'
                });

                // 检查必填字段
                const requiredFields = this.cardDataEditFields.filter(field => field.is_required);
                const missingFields = [];

                this.cardDataEditForm.table_data.forEach((row, rowIndex) => {
                    requiredFields.forEach(field => {
                        const value = row[field.name];
                        if (value === null || value === undefined || value === '') {
                            missingFields.push({
                                row: rowIndex + 1,
                                field: field.display_name || field.name
                            });
                        }
                    });
                });

                if (missingFields.length > 0) {
                    const errorMsg = '以下必填字段未填写，请补充完整：\n' + 
                                  missingFields.slice(0, 5).map(m => `第${m.row}行: ${m.field}`).join('\n') +
                                  (missingFields.length > 5 ? `\n...还有 ${missingFields.length - 5} 个未填字段` : '');
                    this.$message.error(errorMsg);
                    return;
                }

                // 准备提交数据
                const submitData = {
                    status: 'in_progress',
                    table_data: this.cardDataEditForm.table_data
                };

                console.log(' 开始提交流转卡到下一部门:', {
                    cardId: this.currentEditingCard.id,
                    currentStatus: this.currentEditingCard.status
                });

                // 先保存数据
                const saveResponse = await TransferCardAPI.card.updateCardData(
                    this.currentEditingCard.id,
                    submitData
                );

                if (!saveResponse.success) {
                    this.$message.error(saveResponse.message || '保存数据失败');
                    return;
                }

                // 提交到下一部门
                const submitResponse = await TransferCardAPI.flow.submitToNext(
                    this.currentEditingCard.id,
                    submitData
                );

                console.log('📡 提交响应:', submitResponse);

                if (submitResponse.success) {
                    const nextDepartment = submitResponse.data.next_department_name || '未知部门';
                    
                    this.$message({
                        message: `流转卡已成功提交到 ${nextDepartment}`,
                        type: 'success',
                        duration: 3000
                    });

                    // 关闭对话框
                    this.cardDataEditDialogVisible = false;

                    // 刷新流转卡列表
                    this.loadTemplateCards();

                    // 清理数据同步状态
                    this.cleanupDataSync();

                    console.log(' 流转卡提交成功');
                } else {
                    this.$message.error(submitResponse.message || '提交失败');
                }

            } catch (error) {
                if (error !== 'cancel') {
                    console.error(' 提交流转卡失败:', error);
                    this.$message.error('提交失败，请检查网络连接');
                }
            }
        },

        // 启动流转卡流转（管理员或创建人使用）
        async startCardFlow(card) {
            try {
                if (!this.currentUser) {
                    this.$message.warning('请先登录');
                    return;
                }

                await this.$confirm('确定要启动此流转卡的流转吗？\n启动后，流转卡将按照预设的部门顺序流转。', '确认启动', {
                    confirmButtonText: '确定启动',
                    cancelButtonText: '取消',
                    type: 'info'
                });

                const response = await TransferCardAPI.flow.startCardFlow(card.id);

                if (response.success) {
                    this.$message.success('流转卡已启动流转');
                    this.loadTemplateCards();
                } else {
                    this.$message.error(response.message || '启动失败');
                }
            } catch (error) {
                if (error !== 'cancel') {
                    console.error('启动流转卡流转失败:', error);
                    this.$message.error('启动失败');
                }
            }
        },

        // 驳回流转卡
        async rejectCard(card) {
            try {
                if (!this.currentUser) {
                    this.$message.warning('请先登录');
                    return;
                }

                // 获取驳回原因
                const { value: reason } = await this.$prompt('请输入驳回原因', '驳回流转卡', {
                    confirmButtonText: '确定驳回',
                    cancelButtonText: '取消',
                    inputPattern: /.+/,
                    inputErrorMessage: '驳回原因不能为空'
                });

                const response = await TransferCardAPI.flow.rejectCard(card.id, {
                    reject_reason: reason
                });

                if (response.success) {
                    this.$message.success('流转卡已驳回');
                    this.loadTemplateCards();
                } else {
                    this.$message.error(response.message || '驳回失败');
                }
            } catch (error) {
                if (error !== 'cancel') {
                    console.error('驳回流转卡失败:', error);
                    this.$message.error('驳回失败');
                }
            }
        },

        // 获取流转卡流转状态
        async loadCardFlowStatus(cardId) {
            try {
                const response = await TransferCardAPI.flow.getCardFlowStatus(cardId);
                if (response.success) {
                    return response.data;
                } else {
                    console.error('获取流转状态失败:', response.message);
                    return null;
                }
            } catch (error) {
                console.error('获取流转状态失败:', error);
                return null;
            }
        },

        // ========== 流转卡列表中的流转操作方法 ==========

        // 检查是否是最后一个部门
        isLastDepartment(card) {
            return card.is_last_department === 1 || card.is_last_department === true;
        },

        // 检查是否可以在列表中提交流转卡
        canSubmitCard(card) {
            if (!this.currentUser) {
                return false;
            }

            // 管理员始终可以提交
            if (this.currentUser.role === 'admin') {
                return true;
            }

            // 检查流转卡状态
            if (card.status === 'completed' || card.status === 'cancelled') {
                return false;
            }

            // 使用后端返回的permission_level判断
            // 只有'can_submit'权限的部门才能提交（当前处理部门）
            if (card.permission_level === 'can_submit') {
                return true;
            }

            // 'view_only'表示已提交过的部门，只能查看不能提交
            // 'owner'表示创建者，但不是当前处理部门也不能提交
            // 'none'表示无权限
            return false;
        },

        // 检查是否可以启动流转卡流转
        canStartCardFlow(card) {
            if (!this.currentUser) {
                return false;
            }

            // 只有管理员或创建人可以启动流转
            if (this.currentUser.role === 'admin' || 
                card.creator_id === this.currentUser.id) {
                // 只有草稿状态才能启动流转
                return card.status === 'draft';
            }

            return false;
        },

        // 从列表中完成流转卡（最后一个部门使用）
        async completeCardFromList(card) {
            // 完成流转卡和提交到下一部门实际上使用相同的后端接口
            // 后端会自动判断是否是最后一个部门，如果是就完成流转
            return await this.submitCardFromList(card);
        },

        // 从列表中提交流转卡到下一部门
        async submitCardFromList(card) {
            try {
                if (!card || !card.id) {
                    this.$message.error('流转卡信息不完整');
                    return;
                }

                // 确认提交
                const confirmMessage = `确定要将流转卡 ${card.card_number} 提交到下一部门吗？\n提交后，当前部门的填写将被锁定。`;
                await this.$confirm(confirmMessage, '确认提交', {
                    confirmButtonText: '确定提交',
                    cancelButtonText: '取消',
                    type: 'warning'
                });

                // 加载流转卡数据
                const dataResponse = await TransferCardAPI.card.getCardData(card.id);
                if (!dataResponse.success) {
                    this.$message.error('加载流转卡数据失败');
                    return;
                }

                // 检查必填字段
                const fields = dataResponse.data.fields || [];
                const tableData = dataResponse.data.table_data || [];
                const requiredFields = fields.filter(field => field.is_required);
                const missingFields = [];

                tableData.forEach((row, rowIndex) => {
                    requiredFields.forEach(field => {
                        const value = row[field.name];
                        if (value === null || value === undefined || value === '') {
                            missingFields.push({
                                row: rowIndex + 1,
                                field: field.display_name || field.name
                            });
                        }
                    });
                });

                if (missingFields.length > 0) {
                    const errorMsg = '以下必填字段未填写，请点击"填写"按钮补充完整：\n' + 
                                  missingFields.slice(0, 5).map(m => `第${m.row}行: ${m.field}`).join('\n') +
                                  (missingFields.length > 5 ? `\n...还有 ${missingFields.length - 5} 个未填字段` : '');
                    this.$message.error(errorMsg);
                    return;
                }

                // 提交到下一部门
                const submitResponse = await TransferCardAPI.flow.submitToNext(
                    card.id,
                    {
                        status: 'in_progress',
                        table_data: tableData
                    }
                );

                console.log('📡 提交响应:', submitResponse);

                if (submitResponse.success) {
                    const nextDepartment = submitResponse.data.next_department_name || '未知部门';
                    
                    this.$message({
                        message: `流转卡 ${card.card_number} 已成功提交到 ${nextDepartment}`,
                        type: 'success',
                        duration: 3000
                    });

                    // 刷新流转卡列表
                    this.loadTemplateCards();

                    console.log(' 流转卡提交成功');
                } else {
                    this.$message.error(submitResponse.message || '提交失败');
                }

            } catch (error) {
                if (error !== 'cancel') {
                    console.error(' 提交流转卡失败:', error);
                    this.$message.error('提交失败，请检查网络连接');
                }
            }
        }
    }
});
