# 智能轮椅租赁平台

## An Enterprise-grade Smart Wheelchair Rental Platform for the Elderly

* 项目周期: 2025年9月 - 2025年10月 (课程大作业)
* 技术栈: SpringBoot · Vue3 · MySQL · Element-Plus · JWT
* 架构模式: 前后端分离 · MVC三层架构
* 项目状态: ✅ 已完成 (包含完整工程文档)

## 项目概述

这是一个面向失能老人及其家属的智能轮椅B2C租赁服务平台。项目旨在解决智能轮椅购置成本高、维护复杂的市场痛点，通过“以租代购”的创新模式，为老年群体提供经济、便捷、可靠的辅助出行解决方案。
项目亮点
* 完整软件工程实践：独立完成从需求分析 → 系统设计 → 编码实现 → 测试验收的全流程开发
* 企业级文档标准：产出8份符合工业标准的工程文档，总页数超过200页
* 全栈技术应用：SpringBoot后端 + Vue3前端的现代技术架构

## 技术架构图
```html

┌─────────────────────────────────────────────┐
│                  前端展示层                   │
│    Vue3 + Element-Plus + Axios + Router     │
└─────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────┐
│                RESTful API层                 │
│         SpringBoot + Spring MVC + JWT        │
└─────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────┐
│                业务逻辑层                     │
│     Service层 + 事务管理 + 业务规则引擎       │
└─────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────┐
│                数据访问层                     │
│         MyBatis-Plus + MySQL 8.0            │
└─────────────────────────────────────────────┘
```


## 核心功能模块
### 客户端 (家属/护工使用)
* 用户管理：注册/登录、个人信息维护
* 轮椅租赁：浏览商品、查看详情、在线下单
* 订单管理：订单状态跟踪、历史记录查询
* 维修服务：在线报修、进度查询
* 评价反馈：服务评价、建议反馈

### 管理端 (平台运营使用)
* 用户管理：用户信息审核、状态管理
* 轮椅管理：商品上下架、库存管理
* 订单管理：订单审核、状态更新
* 维修管理：工单分配、进度跟踪
* 数据统计：租赁数据可视化分析
* 反馈管理：用户反馈处理与回复

### 数据库设计示例
```sql
-- 轮椅信息表
CREATE TABLE Wheelchair (
    chairId INT PRIMARY KEY AUTO_INCREMENT,
    informationId INT NOT NULL,
    chairStatus ENUM('available', 'rented', 'maintaining') DEFAULT 'available',
    FOREIGN KEY (informationId) REFERENCES WheelchairInfo(informationId)
);

-- 租赁订单表
CREATE TABLE RentalOrder (
    orderId INT PRIMARY KEY AUTO_INCREMENT,
    userId INT NOT NULL,
    chairId INT NOT NULL,
    startTime DATETIME NOT NULL,
    endTime DATETIME NOT NULL,
    totalPrice DECIMAL(10,2) NOT NULL,
    orderStatus ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userId) REFERENCES User(userId),
    FOREIGN KEY (chairId) REFERENCES Wheelchair(chairId)
);
```
### 核心代码展示
SpringBoot控制器示例
```java
/**
 * 租赁订单控制器
 * 提供订单相关的RESTful API接口
 */
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
public class RentalOrderController {
    
    private final RentalOrderService orderService;
    
    /**
     * 创建租赁订单
     * @param request 订单创建请求
     * @return 创建成功的订单信息
     */
    @PostMapping
    public ResponseEntity<ApiResponse<RentalOrderDTO>> createOrder(
            @Valid @RequestBody CreateOrderRequest request) {
        
        // 参数验证
        if (request.getStartTime().isBefore(LocalDateTime.now())) {
            throw new BusinessException("租赁开始时间不能早于当前时间");
        }
        
        if (request.getDuration() < 1) {
            throw new BusinessException("租赁时长至少为1天");
        }
        
        // 调用服务层创建订单
        RentalOrderDTO orderDTO = orderService.createOrder(request);
        
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("订单创建成功", orderDTO));
    }
    
    /**
     * 获取用户订单列表
     * @param userId 用户ID
     * @param status 订单状态筛选
     * @param page 页码
     * @param size 每页大小
     * @return 分页订单列表
     */
    @GetMapping("/user/{userId}")
    public ResponseEntity<ApiResponse<PageResult<RentalOrderDTO>>> getUserOrders(
            @PathVariable Long userId,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        
        PageResult<RentalOrderDTO> orders = orderService.getUserOrders(userId, status, page, size);
        
        return ResponseEntity.ok(ApiResponse.success("查询成功", orders));
    }
}

```

2. 业务服务层
```java
/**
 * 租赁订单服务实现
 * 处理订单相关的核心业务逻辑
 */
@Service
@Transactional
@RequiredArgsConstructor
@Slf4j
public class RentalOrderServiceImpl implements RentalOrderService {
    
    private final RentalOrderMapper orderMapper;
    private final WheelchairMapper wheelchairMapper;
    private final UserMapper userMapper;
    private final PriceCalculator priceCalculator;
    
    @Override
    public RentalOrderDTO createOrder(CreateOrderRequest request) {
        // 1. 验证用户存在
        User user = userMapper.selectById(request.getUserId());
        if (user == null) {
            throw new BusinessException("用户不存在");
        }
        
        // 2. 验证轮椅可用
        Wheelchair wheelchair = wheelchairMapper.selectById(request.getChairId());
        if (wheelchair == null || !"available".equals(wheelchair.getStatus())) {
            throw new BusinessException("轮椅不可用");
        }
        
        // 3. 验证时间冲突
        boolean hasConflict = orderMapper.hasTimeConflict(
            request.getChairId(), 
            request.getStartTime(), 
            request.getEndTime()
        );
        if (hasConflict) {
            throw new BusinessException("该时间段轮椅已被预订");
        }
        
        // 4. 计算租赁费用
        BigDecimal totalPrice = priceCalculator.calculateRentalPrice(
            wheelchair.getDailyPrice(),
            request.getStartTime(),
            request.getEndTime()
        );
        
        // 5. 创建订单实体
        RentalOrder order = RentalOrder.builder()
            .userId(request.getUserId())
            .chairId(request.getChairId())
            .startTime(request.getStartTime())
            .endTime(request.getEndTime())
            .totalPrice(totalPrice)
            .deliveryAddress(request.getDeliveryAddress())
            .contactPhone(request.getContactPhone())
            .status("pending")
            .build();
        
        // 6. 保存订单并更新轮椅状态
        orderMapper.insert(order);
        wheelchair.setStatus("rented");
        wheelchairMapper.updateById(wheelchair);
        
        log.info("订单创建成功: 订单ID={}, 用户ID={}, 轮椅ID={}", 
            order.getOrderId(), order.getUserId(), order.getChairId());
        
        return convertToDTO(order);
    }
    
    /**
     * 计算订单价格
     */
    private BigDecimal calculatePrice(Wheelchair wheelchair, CreateOrderRequest request) {
        long days = ChronoUnit.DAYS.between(
            request.getStartTime().toLocalDate(),
            request.getEndTime().toLocalDate()
        );
        
        BigDecimal dailyPrice = wheelchair.getDailyPrice();
        BigDecimal total = dailyPrice.multiply(BigDecimal.valueOf(days));
        
        // 长租优惠：超过7天打9折
        if (days > 7) {
            total = total.multiply(new BigDecimal("0.9"));
        }
        
        return total.setScale(2, RoundingMode.HALF_UP);
    }
}
```
3. Vue3 组件示例
```javascript
<!-- WheelchairList.vue - 轮椅列表组件 -->
<template>
  <div class="wheelchair-list">
    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索轮椅型号或功能"
        @input="handleSearch"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select v-model="filterType" placeholder="类型筛选" @change="loadData">
        <el-option label="全部" value="" />
        <el-option label="电动轮椅" value="electric" />
        <el-option label="手动轮椅" value="manual" />
      </el-select>
    </div>
    
    <!-- 轮椅列表 -->
    <div v-if="loading" class="loading">
      <el-skeleton :rows="6" animated />
    </div>
    
    <div v-else class="list-container">
      <el-row :gutter="20">
        <el-col
          v-for="chair in wheelchairs"
          :key="chair.chairId"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <wheelchair-card
            :chair="chair"
            @rent="handleRent"
          />
        </el-col>
      </el-row>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper"
        @current-change="handlePageChange"
      />
    </div>
    
    <!-- 空状态 -->
    <el-empty
      v-if="!loading && wheelchairs.length === 0"
      description="暂无可用轮椅"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import WheelchairCard from './WheelchairCard.vue'
import { fetchWheelchairList } from '@/api/wheelchair'

// 响应式数据
const wheelchairs = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const filterType = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      keyword: searchKeyword.value,
      type: filterType.value
    }
    
    const res = await fetchWheelchairList(params)
    wheelchairs.value = res.data.list
    total.value = res.data.total
  } catch (error) {
    ElMessage.error('加载轮椅列表失败')
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索防抖处理
let searchTimer = null
const handleSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadData()
  }, 500)
}

// 页面切换
const handlePageChange = (page) => {
  currentPage.value = page
  loadData()
}

// 租赁按钮点击
const handleRent = (chairId) => {
  // 跳转到租赁页面
  router.push(`/rent/${chairId}`)
}

// 初始化加载
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.wheelchair-list {
  padding: 20px;
}

.filter-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.loading {
  padding: 40px 0;
}

.list-container {
  margin-top: 20px;
}
</style>
```