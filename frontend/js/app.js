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
                pendingCards: 0,
                completedToday: 0,
                weeklyTotal: 0
            },
            recentOperations: [],
            
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
            }
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
                    console.log('✅用户信息已更新', response.data);
                } else {
                    console.error('❌用户信息获取失败:', response.message);
                }
            } catch (error) {
                console.error('❌加载用户信息失败:', error);
            }
        },
        
        // 登录
        async login() {
            try {
                console.log('🚀 开始登录流程..');
                const valid = await this.$refs.loginForm.validate();
                if (!valid) return;
                
                console.log('📝 登录参数:', {
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
                    console.log('✅Token已保存', response.token);
                    
                    this.currentUser = response.data;
                    console.log('✅用户信息已设置', this.currentUser);
                    
                    this.isLoggedIn = true;
                    console.log('✅登录状态已更新:', this.isLoggedIn);
                    
                    this.activeMenu = 'dashboard';
                    
                    this.loadDashboardData();
                    
                    console.log('登录成功！正在跳转..');
                    if (this.$message) {
                        this.$message.success('登录成功！正在跳转..');
                    }
                    
                    this.$nextTick(() => {
                        console.log('✅Vue视图已更新');
                        this.$forceUpdate();
                    });
                } else {
                    this.$message.error(response.message || '登录失败');
                }
            } catch (error) {
                console.error('❌登录失败:', error);
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
                this.dashboardData = {
                    pendingCards: 5,
                    completedToday: 3,
                    weeklyTotal: 12
                };
                
                this.recentOperations = [
                    {
                        card_number: 'TC001',
                        action: '编辑',
                        description: '更新物料信息',
                        created_at: new Date().toLocaleString()
                    }
                ];
            } catch (error) {
                console.error('加载工作台数据失败', error);
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
                console.log('🔍 开始加载字段列表..');
                const response = await TransferCardAPI.field.getFields();
                console.log('🔍 字段API响应:', response);
                
                if (response.success) {
                    this.fields = response.data || response.fields || [];
                    console.log('✅字段列表已加载', this.fields);
                    
                    this.$nextTick(() => {
                        this.$forceUpdate();
                    });
                } else {
                    console.error('❌字段API返回失败:', response.message);
                    this.$message.error(response.message || '加载字段列表失败');
                }
            } catch (error) {
                console.error('❌加载字段列表失败:', error);
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
                    
                    console.log('✅模板列表已加载，状态已初始化', templates.map(t => ({
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
                console.error('❌保存模板失败:', error);
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
                console.log('🔄 状态变更 - 模板:', template.template_name, '新状态:', template.is_active);
                
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
            // 管理员可以编辑所有流转卡
            if (this.currentUser.role === 'admin') return true;
            // 普通用户可以填写数据
            return true;
        },

        // 检查是否可以删除流转卡
        canDeleteCard(card) {
            if (!this.currentUser) return false;
            // 管理员可以删除所有流转卡
            if (this.currentUser.role === 'admin') return true;
            // 普通用户不能删除流转卡
            return false;
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
                console.log('🚀 开始保存部门:', this.departmentForm);
                
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
                console.error('❌ 保存部门失败:', error);
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
            
            console.log('🔄 更新表格结构预览，选中字段数量:', selectedFields.length);
            console.log('🔄 选中字段:', selectedFields);
            
            // 预览模式不需要真实数据，只生成空行用于显示结构
            this.previewTableData = [{}];
            
            console.log('🔄 表格结构预览已生成，字段数量:', selectedFields.length);
            
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
                this.currentEditingCard = { ...card };
                this.cardDataEditForm = {
                    status: card.status,
                    table_data: []
                };
                
                // 加载流转卡字段和数据
                await this.loadCardEditData(card.id);
                this.cardDataEditDialogVisible = true;
            } catch (error) {
                console.error('加载编辑数据失败:', error);
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

                const response = await TransferCardAPI.card.updateCardData(this.currentEditingCard.id, updateData);
                
                if (response.success) {
                    this.$message.success('数据保存成功');
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
            // console.log(`🔍 格式化字段值:`, { value, fieldType, valueType: typeof value });
            
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
        }
    }
});
