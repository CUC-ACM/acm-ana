# CUC-ACM Score-Analysis

## Release

> 在 [https://github.com/CUC-ACM/acm-ana/releases/tag/v0.0.9](https://github.com/CUC-ACM/acm-ana/releases/tag/v0.0.9) 中下载输出的 `Excel` 表格

|  关键字  |  对应   |   比赛平台    |
| :------: | :-----: | :-----------: |
| prophase | 1~5 场  | 牛客 & Vjudge |
|  Basic   | 6~8 场  |    Vjudge     |
|   div1   | 9~16 场 |    Vjudge     |
|   div2   | 9~16 场 |    Vjudge     |

## 比赛出题人须知

### Vjudge

- 比赛不要设置密码
- 比赛 **结束时间** **准确设置** 为对于比赛 **当天** 的时间，不要先随便设置一个时间到后面再改
- 比赛名称需要按照特定的 **前缀统一命名**，如 `CUC-ACM-2023秋季学期新生练习xx-xx`

#### 前期(1~5 次)命名规范

```
CUC-ACM-2023秋季学期新生练习10.18
CUC-ACM-2023秋季学期新生练习10.25
```

#### 中期(6~8 次)命名规范

> 相对于前期，中期的比赛名称需要在前面加上 `基础` 二字

```
CUC-ACM-2023秋季学期新生基础练习xx.xx
CUC-ACM-2023秋季学期新生基础练习xx.xx
```

#### 后期(9~16 次)命名规范

此时分为 `div1` 和 `div2` 两个比赛，所以需要分别命名

```
CUC-ACM-2023秋季学期新生练习-div1-xx.xx
CUC-ACM-2023秋季学期新生练习-div2-xx.xx
```

### 牛客

#### 命名

- 命名为统一为（用汉字数字标明场次）

```
CUC2023秋季新生训练第四场
CUC2023秋季新生训练第五场
```

#### 添加管理员

> 首先需要将 `爬虫使用的账户` 加入到 `牛客比赛` 的 `管理员` 中
>
> 加入方法详情见 https://docs.qq.com/doc/DTHlmT1FDSWRJcmVo
>
> 省流：使用 `比赛创建者的账号` 点击 https://ac.nowcoder.com/acm/admin/self/rejudge?contestId=67703
>
> 将上述链接中的 `contestId` 改为对应比赛的 `contestId` 即可

## 积分排名计算方法

### 积分计算方法

> 对于每一场比赛，我们都会计算一次积分，积分计算方法如下：

$$
\text{score} = \text{min}(100, 比赛期间得分 + 比赛后补题分)
$$

#### 比赛期间得分

> 此排名以在对于平台 _比赛结束时_ 的排名为准

|  排名区间  | 得分  |
| :--------: | :---: |
|  $(0,20]$  | $100$ |
| $(20,40]$  | $90$  |
| $(40,60]$  | $80$  |
| $(60,80]$  | $70$  |
| $(80,100]$ | $60$  |

#### 比赛后补题分

> 比赛后补题分截止以 `比赛结束` 开始计算的 7 天内。
>
> 例如比赛结束时间为 `18:00` ，则补题分截止时间为 `18:00 + 7天`

$$
比赛后补题分 = 补题数\times 6
$$

## 后期维护人员须知

### 配置

将每次比赛的 **前缀名称** 如 `CUC-ACM-2023秋季学期新生练习` 填入 [config.yaml](./config.yaml) 中的 `title_prefix` 字段中

### `VJUDGE_COOKIE` 环境变量

> 在下面情况下需要设置 `VJUDGE_COOKIE` 环境变量

- 调用 `acmana/crawler/vjudge/user_info.py` 中爬取 `Vjudge 用户 ID`
- `Github Actions` 中的 `CICD` `unittest`（需在 `Github` 中设置 `Secrets`）

### `NOWCODER_COOKIE` 环境变量

> 由于牛客对于 `非管理员用户` 只能看到比赛的前 10 页提交，无法查看到所有提交来统计 `补题数`，所以在所有情况下都需要设置 `NOWCODER_COOKIE` 环境变量

### 运行方法

#### 本地运行

```bash
python -m acmana
```

#### Github Actions

建议将每一个学期新建一个不同的分支，然后将 [config.yaml](./config.yaml) `push` 到对应的分支中。

记得将 [https://github.com/CUC-ACM/acm-ana/actions/workflows/create_release.yaml](https://github.com/CUC-ACM/acm-ana/actions/workflows/create_release.yaml) `Enable Workflow` 开启
