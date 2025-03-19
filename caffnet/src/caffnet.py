from typing import Dict
import torch
import torch.nn as nn
import torch.nn.functional as F



class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, mid_channels=None):
        if mid_channels is None:
            mid_channels = out_channels
        super(ConvBlock, self).__init__()

        # 左边
        # 第1个3x3卷积层
        self.conv1 = nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1)
        # BN层
        self.bn1 = nn.BatchNorm2d(mid_channels)
        # RELU层
        self.relu1 = nn.ReLU(inplace=True)
        # 第2个3x3卷积层
        self.conv2 = nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1)
        # BN层
        self.bn2 = nn.BatchNorm2d(out_channels)
        # RELU层
        self.relu2 = nn.ReLU(inplace=True)

        # 右边
        # 1x1卷积层用于调整通道数
        self.conv_1x1 = nn.Conv2d(in_channels, out_channels, kernel_size=1)
        # BN层
        self.bn_1x1 = nn.BatchNorm2d(out_channels)
        # 最后的ReLU层用于输出
        self.relu_final = nn.ReLU(inplace=True)

    def forward(self, x):
        # 打印输入x的形状
        # print("Input shape:", x.shape)

        # 左边路径
        x1 = self.relu1(self.bn1(self.conv1(x)))
        # print("After conv1 and bn1 and relu1 shape:", x1.shape)
        x1 = self.relu2(self.bn2(self.conv2(x1)))
        # print("After conv2 and bn2 and relu2 shape:", x1.shape)

        # 右边路径
        x2 = self.relu_final(self.bn_1x1(self.conv_1x1(x)))
        # print("After conv_1x1 and bn_1x1 and relu_final shape:", x2.shape)

        # 将两个结果进行逐元素相加
        out = x1 + x2
        # 打印输出out的形状
        # print("Output shape:", out.shape)

        return out


class DBPF(nn.Module):
    def __init__(self, in_channels):
        super(DBPF, self).__init__()
        self.avg_pool = nn.AvgPool2d(kernel_size=2, stride=2)
        self.max_pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv1x1 = nn.Conv2d(in_channels * 2, in_channels, kernel_size=1, stride=1, bias=False)
        self.conv1x1_adjust_x = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, bias=False)
        self.conv1x1_adjust_y = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, bias=False)
        self.conv1x1_adjust_f = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, bias=False)

    def forward(self, E_i: torch.Tensor) -> torch.Tensor:
        # 打印输入特征图的形状
        # print(f"Input shape: {E_i.shape}")

        # 将最大池化和平均池化结果拼接
        pooled = torch.cat((self.avg_pool(E_i), self.max_pool(E_i)), dim=1)
        # print(f"Pooled shape: {pooled.shape}")

        # 通过1x1卷积来合并通道
        F_i = self.conv1x1(pooled)
        # print(f"Conv1x1 shape: {F_i.shape}")

        # 沿x，y方向平均池化
        avg_pooled_x = F.avg_pool2d(F_i, kernel_size=(1, 2), stride=(1, 2))
        avg_pooled_y = F.avg_pool2d(F_i, kernel_size=(2, 1), stride=(2, 1))
        # print(f"Avg pooled x shape: {avg_pooled_x.shape}")
        # print(f"Avg pooled y shape: {avg_pooled_y.shape}")

        # 在上采样之前，使用1x1卷积调整avg_pooled_x和avg_pooled_y
        adjusted_avg_pooled_x = self.conv1x1_adjust_x(avg_pooled_x)
        adjusted_avg_pooled_y = self.conv1x1_adjust_y(avg_pooled_y)
        # print(f"Adjusted avg pooled x shape: {adjusted_avg_pooled_x.shape}")
        # print(f"Adjusted avg pooled y shape: {adjusted_avg_pooled_y.shape}")

        # 确保上采样操作恢复到F_i(两种池化后)的尺寸
        target_height = F_i.size(2)
        target_width = F_i.size(3)
        F_ix = F.interpolate(adjusted_avg_pooled_x, size=(target_height, target_width), mode='bilinear',
                             align_corners=False)
        F_iy = F.interpolate(adjusted_avg_pooled_y, size=(target_height, target_width), mode='bilinear',
                             align_corners=False)
        # print(f"F_ix shape: {F_ix.shape}")
        # print(f"F_iy shape: {F_iy.shape}")

        # 逐元素相加并再次通过1x1卷积
        fused_features = self.conv1x1_adjust_f(F_ix + F_iy)
        # print(f"Fused features shape: {fused_features.shape}")

        # 与原始1x1卷积后的特征图F_i进行逐元素相加得到最终输出
        E_i_prime = fused_features + F_i
        # print(f"Output shape: {E_i_prime.shape}")

        return E_i_prime


class Classifier(nn.Module):
    def __init__(self, in_channels, out_channels, mid_channels=None):
        if mid_channels is None:
            mid_channels = out_channels
        super(Classifier, self).__init__()
        self.conv_3x3 = nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1)
        self.conv_1x1 = nn.Conv2d(mid_channels, out_channels, kernel_size=1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.sigmoid(self.conv_1x1(self.conv_3x3(x)))

        return x


class Down(nn.Sequential):
    def __init__(self, in_channels, out_channels):
        super(Down, self).__init__(
            ConvBlock(in_channels, out_channels),
            DBPF(in_channels)
        )


# class CaFF(nn.Module):
#     def __init__(self, in_channels):
#         super(CaFF, self).__init__()
#         self.in_channels = in_channels
#         self.classifier = Classifier(in_channels, 1)
#         # 初始化权重矩阵W_Qi, W_Ki, W_Vi
#         self.W_Qi = nn.Parameter(torch.Tensor(in_channels, in_channels))
#         self.W_Ki = nn.Parameter(torch.Tensor(in_channels, in_channels))
#         self.W_Vi = nn.Parameter(torch.Tensor(in_channels, in_channels))
#         self.initialize_weights()
#
#     def initialize_weights(self):
#         # 使用Xavier初始化或者其他您喜欢的初始化方法
#         nn.init.xavier_uniform_(self.W_Qi)
#         nn.init.xavier_uniform_(self.W_Ki)
#         nn.init.xavier_uniform_(self.W_Vi)
#
#     def forward(self, D_i, E_i):
#         # print(f'D_i.shape: {D_i.shape}')
#         # print(f'E_i.shape: {E_i.shape}')
#         diff_y = E_i.size()[2] - D_i.size()[2]
#         diff_x = E_i.size()[3] - D_i.size()[3]
#         # 对D_i的上下左右进行插值，使得与E_i形状一致
#         # padding_left, padding_right, padding_top, padding_bottom
#         D_i = F.pad(D_i, [diff_x // 2, diff_x - diff_x // 2,
#                           diff_y // 2, diff_y - diff_y // 2])
#         # print(f'D_i.shape: {D_i.shape}')
#
#         # Classifier处理解码器传来的D_i得到粗略掩码M_i
#         M_i = self.classifier(D_i)
#         # print(f'M_i.shape: {M_i.shape}')
#         # 逐元素相乘得到加权的解码器特征图M_i * D_i
#         M_D_i = M_i * D_i
#         # print(f'M_D_i.shape: {M_D_i.shape}')
#         # 生成血管原型P，使用全局平均池化
#         P = torch.mean(M_D_i, dim=(2, 3), keepdim=True)  # P的维度现在是(N, C, 1, 1)
#         # print(f'P.shape: {P.shape}')
#
#         # 算K_i，V_i
#         # 去掉P的最后一维，从(N, C, 1, 1)变为(N, C, 1)，使得倒数第2维C与W_Ki和W_Vi的最后一维匹配，能做矩阵乘法
#         P = P.squeeze(-1)
#         # print(f'P.shape: {P.shape}')
#         # print(f'self.W_Ki.shape: {self.W_Ki.shape}')
#         # print(f'self.W_Vi.shape: {self.W_Vi.shape}')
#         # 使用权重矩阵W_Ki, 注意这里P_transposed的最后一个维度与W_Ki的行向量相乘
#         K_i = torch.matmul(self.W_Ki, P)  # K_i的维度是(N, C, 1)
#         # print(f'K_i.shape: {K_i.shape}')
#         V_i = torch.matmul(self.W_Vi, P)  # V_i的维度是(N, C, 1)
#         # print(f'V_i.shape: {V_i.shape}')
#         V_i = V_i.permute(0, 2, 1)  # 将V后两维转置
#         # print(f'V_i.shape: {V_i.shape}')
#
#         # 算Q_i
#         E_i_copy = E_i.view(E_i.size(0), E_i.size(1), -1)  # 换成(N,C,HW)，便于乘法
#         # E_i = E_i.permute(2, 1, 0) # 换成(HW,C,N)
#         # print(f'E_i_copy.shape: {E_i_copy.shape}')
#         # print(f'self.W_Qi.shape: {self.W_Qi.shape}')
#
#         Q_i = torch.matmul(self.W_Qi, E_i_copy)  # Q_i也是(N,C,HW)
#         # print(f'Q_i.shape: {Q_i.shape}')
#         Q_i_transposed = Q_i.permute(0, 2, 1)  # 转置，换成(N,HW,C)
#         # print(f'Q_i_transposed.shape: {Q_i_transposed.shape}')
#
#         # 不用做softmax，因为矩阵只有一个key
#         QK_C = torch.matmul(Q_i_transposed, K_i) / pow(self.in_channels, 0.5)
#         # print(f'QK_C.shape: {QK_C.shape}')
#         # 转置回来后修改维度
#         right_part = torch.matmul(QK_C, V_i).permute(0, 2, 1).view(D_i.size(0), D_i.size(1), D_i.size(2), D_i.size(3))
#         # print(f'right_part.shape: {right_part.shape}')
#
#         return E_i + right_part


class CaFF(nn.Module): # 自己想的那种解决方法
    def __init__(self, in_channels):
        super(CaFF, self).__init__()
        self.in_channels = in_channels
        self.classifier = Classifier(in_channels, 1)
        # 初始化权重矩阵W_Qi, W_Ki, W_Vi
        self.W_Qi = nn.Parameter(torch.Tensor(in_channels, in_channels))
        self.W_Ki = nn.Parameter(torch.Tensor(in_channels, in_channels))
        self.W_Vi = nn.Parameter(torch.Tensor(in_channels, in_channels))
        self.initialize_weights()

    def initialize_weights(self):
        # 使用Xavier初始化或者其他您喜欢的初始化方法
        nn.init.xavier_uniform_(self.W_Qi)
        nn.init.xavier_uniform_(self.W_Ki)
        nn.init.xavier_uniform_(self.W_Vi)

    def forward(self, D_i, E_i):
        # print(f'D_i.shape: {D_i.shape}')
        # print(f'E_i.shape: {E_i.shape}')
        diff_y = E_i.size()[2] - D_i.size()[2]
        diff_x = E_i.size()[3] - D_i.size()[3]
        # 对D_i的上下左右进行插值，使得与E_i形状一致
        # padding_left, padding_right, padding_top, padding_bottom
        D_i = F.pad(D_i, [diff_x // 2, diff_x - diff_x // 2,
                          diff_y // 2, diff_y - diff_y // 2])
        # print(f'D_i.shape: {D_i.shape}')
        # Classifier处理解码器传来的D_i得到粗略掩码M_i
        M_i = self.classifier(D_i)
        # print(f'M_i.shape: {M_i.shape}')
        # 逐元素相乘得到加权的解码器特征图M_i * D_i
        M_D_i = M_i * D_i
        # print(f'M_D_i.shape: {M_D_i.shape}')
        # 生成血管原型P，使用全局平均池化
        P = torch.mean(M_D_i, dim=(2, 3), keepdim=True)  # P的维度现在是(N, C, 1, 1)
        # print(f'P.shape: {P.shape}')

        # 算K_i，V_i
        # 去掉P的最后一维，从(N, C, 1, 1)变为(N, C, 1)，使得倒数第2维C与W_Ki和W_Vi的最后一维匹配，能做矩阵乘法
        P = P.squeeze(-1)
        # print(f'P.shape: {P.shape}')
        # print(f'self.W_Ki.shape: {self.W_Ki.shape}')
        # print(f'self.W_Vi.shape: {self.W_Vi.shape}')
        # 使用权重矩阵W_Ki, 注意这里P_transposed的最后一个维度与W_Ki的行向量相乘
        K_i = torch.matmul(self.W_Ki, P)  # K_i的维度是(N, C, 1)
        # print(f'K_i.shape: {K_i.shape}')
        K_i = K_i.permute(0, 2, 1)  # # K_i的维度是(N, 1, C)
        # print(f'K_i.shape: {K_i.shape}')
        K_i = K_i.unsqueeze(1)  # K_i先增加一个维度
        # print(f'K_i.shape: {K_i.shape}')
        K_i = K_i.repeat(1, self.in_channels, 1, 1)  # 然后在新增加的维度上重复
        # print(f'K_i.shape: {K_i.shape}')
        V_i = torch.matmul(self.W_Vi, P)  # V_i的维度是(N, C, 1)
        # print(f'V_i.shape: {V_i.shape}')
        # V_i = V_i.permute(0, 2, 1)  # 将V后两维转置
        V_i = V_i.unsqueeze(1)  # V_i增加一个维度
        # print(f'V_i.shape: {V_i.shape}')
        V_i = V_i.repeat(1, self.in_channels, 1, 1)  # 然后在新增加的维度上重复
        # print(f'V_i.shape: {V_i.shape}')

        # 算Q_i
        E_i_copy = E_i.view(E_i.size(0), E_i.size(1), -1)  # 换成(N,C,HW)，便于乘法
        # E_i = E_i.permute(2, 1, 0) # 换成(HW,C,N)
        # print(f'E_i_copy.shape: {E_i_copy.shape}')
        # print(f'self.W_Qi.shape: {self.W_Qi.shape}')

        Q_i = torch.matmul(self.W_Qi, E_i_copy)  # Q_i也是(N,C,HW)
        # print(f'Q_i.shape: {Q_i.shape}')
        Q_i = Q_i.unsqueeze(-1)  # 给Q_i增维度
        # print(f'Q_i.shape: {Q_i.shape}')
        # Q_i_transposed = Q_i.permute(0, 2, 1) # 转置，换成(N,HW,C)
        # print(f'Q_i_transposed.shape: {Q_i_transposed.shape}')

        # 相乘后在最后一维上应用softmax
        # s_QK = F.softmax(torch.matmul(Q_i, K_i)/ torch.sqrt(torch.tensor([self.in_channels])), dim=-1) # 按论文要求要除，其实dk是1
        s_QK = F.softmax(torch.matmul(Q_i, K_i), dim=-1)
        # print(f's_QK.shape: {s_QK.shape}')
        right_part = torch.matmul(s_QK, V_i).squeeze(-1).view(D_i.size(0), D_i.size(1), D_i.size(2), D_i.size(3))
        # print(f'right_part.shape: {right_part.shape}')

        return E_i + right_part

class CaFFNet(nn.Module):
    def __init__(self,
                 in_channels: int = 1,
                 num_classes: int = 2,
                 bilinear: bool = True,
                 base_c: int = 64):
        super(CaFFNet, self).__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.bilinear = bilinear

        # 下采样
        self.down_conv_block1 = ConvBlock(in_channels, base_c)
        self.caff1 = CaFF(base_c)
        self.dbpf1 = DBPF(base_c)
        self.down_conv_block2 = ConvBlock(base_c, base_c * 2)
        self.caff2 = CaFF(base_c * 2)
        self.dbpf2 = DBPF(base_c * 2)
        self.down_conv_block3 = ConvBlock(base_c * 2, base_c * 4)
        self.caff3 = CaFF(base_c * 4)
        self.dbpf3 = DBPF(base_c * 4)

        # 底部
        self.bottom_conv = ConvBlock(base_c * 4, base_c * 8)

        # 上采样
        self.up_expand3 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.up_conv_block3 = ConvBlock(base_c * 8, base_c * 4)
        self.up_expand2 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.up_conv_block2 = ConvBlock(base_c * 8, base_c * 2, base_c * 4)
        self.up_expand1 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.up_conv_block1 = ConvBlock(base_c * 4, base_c, base_c * 2)
        self.final_classifier = Classifier(base_c * 2, num_classes, base_c)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:

        print(f'x.shape: {x.shape}')
        # 下采样
        e1 = self.down_conv_block1(x)  # 第1层给caff1和下一层的值
        # print(f'e1.shape: {e1.shape}')
        x = self.dbpf1(e1)
        # print(f'x.shape: {x.shape}')
        e2 = self.down_conv_block2(x)  # 第2层给caff2和下一层的值
        # print(f'e2.shape: {e2.shape}')
        x = self.dbpf2(e2)
        # print(f'x.shape: {x.shape}')
        e3 = self.down_conv_block3(x)  # 第3层给caff3和下一层的值
        # print(f'e3.shape: {e3.shape}')
        x = self.dbpf3(e3)
        # print(f'x.shape: {x.shape}')

        # 底部
        x = self.bottom_conv(x)
        # print(f'x.shape: {x.shape}')

        # 上采样
        x = self.up_expand3(x)
        # print(f'x.shape: {x.shape}')
        d3 = self.up_conv_block3(x)  # 上采样过程中给第3层caff3和上一层的值
        # print(f'd3.shape: {d3.shape}')
        t3 = self.caff3(d3, e3)
        # print(f't3.shape: {t3.shape}')
        # 计算y和x轴上两者的大小差值
        diff_y3 = t3.size()[2] - d3.size()[2]
        diff_x3 = t3.size()[3] - d3.size()[3]
        # 对其上下左右进行插值
        # padding_left, padding_right, padding_top, padding_bottom
        d3 = F.pad(d3, [diff_x3 // 2, diff_x3 - diff_x3 // 2,
                        diff_y3 // 2, diff_y3 - diff_y3 // 2])
        x = torch.cat([t3, d3], dim=1)
        # print(f'x.shape: {x.shape}')

        x = self.up_expand2(x)
        # print(f'x.shape: {x.shape}')
        d2 = self.up_conv_block2(x)  # 上采样过程中给第2层caff2和上一层的值
        # print(f'd2.shape: {d2.shape}')
        t2 = self.caff2(d2, e2)
        # print(f't2.shape: {t2.shape}')
        # 计算y和x轴上两者的大小差值
        diff_y2 = t2.size()[2] - d2.size()[2]
        diff_x2 = t2.size()[3] - d2.size()[3]
        # 对其的上下左右进行插值
        # padding_left, padding_right, padding_top, padding_bottom
        d2 = F.pad(d2, [diff_x2 // 2, diff_x2 - diff_x2 // 2,
                        diff_y2 // 2, diff_y2 - diff_y2 // 2])
        x = torch.cat([t2, d2], dim=1)
        # print(f'x.shape: {x.shape}')

        x = self.up_expand1(x)
        # print(f'x.shape: {x.shape}')
        d1 = self.up_conv_block1(x)  # 上采样过程中给第1层caff1和上一层的值
        # print(f'd1.shape: {d1.shape}')
        t1 = self.caff1(d1, e1)
        # print(f't1.shape: {t1.shape}')
        # 计算y和x轴上两者的大小差值
        diff_y1 = t1.size()[2] - d1.size()[2]
        diff_x1 = t1.size()[3] - d1.size()[3]
        # 对x1的上下左右进行插值
        # padding_left, padding_right, padding_top, padding_bottom
        d1 = F.pad(d1, [diff_x1 // 2, diff_x1 - diff_x1 // 2,
                        diff_y1 // 2, diff_y1 - diff_y1 // 2])
        x = torch.cat([t1, d1], dim=1)
        # print(f'x.shape: {x.shape}')

        x = self.final_classifier(x)
        # print(f'x.shape: {x.shape}')

        return {"out": x}


if __name__ == '__main__':
    # 假设输入特征图D_i和E_i的通道数为64
    in_channels = 64
    CaFF_module = CaFF(in_channels)

    # 假设D_i和E_i的形状为[batch_size, channels, height, width]
    D_i = torch.randn(3, 64, 32, 32)
    E_i = torch.randn(3, 64, 32, 32)

    # 前向传播CaFF模块
    T_i = CaFF_module(D_i, E_i)
    print(T_i.shape)



    img = torch.randn(4, 3, 565, 584)
    caffnet = CaFFNet(in_channels=3, num_classes=2, base_c=4)
    out = caffnet(img)
    print(out['out'].shape)
