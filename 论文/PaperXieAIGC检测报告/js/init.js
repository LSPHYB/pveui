// 记录当前选中AI内容
let aiContentIndex = 0;
// 初始化饼图
const initEchartsPie = () => {
    const customChart = echarts.init(document.querySelector('.echarts-pie'))
    const pieData = JSON.parse(document.querySelector('.echarts-pie-data').textContent);
    customChart.setOption({
        tooltip: {
            trigger: 'item'
        },
        legend: {
            right: '0%',
            top: 'center',
            orient: 'vertical',
            itemWidth: 10,
            itemHeight: 10,
            itemGap: 20,
            borderRadius: 10
        },
        series: [
            {
                type: 'pie',
                radius: ['65%', '95%'],
                center: ['30%', '50%'],
                avoidLabelOverlap: false,
                padAngle: 5,
                itemStyle: {
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                // labelLine: {
                //     show: false
                // },
                data: [
                    { value: pieData[0], name: `高度疑似AIGC占全文比: ${pieData[0]}%`, itemStyle: { color: '#FF3B30' } },
                    { value: pieData[1], name: `中度疑似AIGC占全文比: ${pieData[1]}%`, itemStyle: { color: '#FF9500' } },
                    { value: pieData[2], name: `低度疑似AIGC占全文比: ${pieData[2]}%`, itemStyle: { color: '#52B767' } },
                    { value: pieData[3], name: `不予检测文字占全文比: ${pieData[3]}%`, itemStyle: { color: '#DDDDDD' } },
                ]
            }
        ]

    });
}
// 初始化自定义
const initEchartsCustom = () => {
    // 获取dom
    const customChart = echarts.init(document.querySelector('.echarts-custom'));
    // 自定义数据
    const data = JSON.parse(document.querySelector('.echarts-custom-data').textContent);
    // 获取颜色
    const getColor = (value) => {
        if (value > 0.7 && value <= 1) return '#70DB93';
        if (value > 0.3 && value <= 0.7) return '#ff8650';
        if (value > -2 && value <= 0.3) return '#f95b5b';
    }
    // 获取文本
    const getText = (value) => {
        if (value > 0.7 && value <= 1) return '低度疑似AIGC';
        if (value > 0.3 && value <= 0.7) return '中度疑似AIGC';
        if (value > -2 && value <= 0.3) return '高度疑似AIGC';
    }
    // 实现渲染每一项
    const renderItem = (params, api) => {
        var categoryIndex = api.value(0);
        var start = api.coord([api.value(1), categoryIndex]);
        var end = api.coord([api.value(2), categoryIndex]);
        var height = api.size([0, 1])[1];
        var rectShape = echarts.graphic.clipRectByRect(
            {
                x: start[0],
                y: start[1] - height,
                width: end[0] - start[0],
                height: height
            },
            {
                x: params.coordSys.x,
                y: params.coordSys.y,
                width: params.coordSys.width,
                height: params.coordSys.height
            }
        );
        return (
            rectShape && {
                type: 'rect',
                transition: ['shape'],
                shape: rectShape,
                style: api.style({
                    stroke: api.style().fill,
                })
            }
        );
    }
    // 自定义数据结构
    const customData = data.map((item, index) => {
        return {
            name: `第${index + 1}段`,
            value: [0, index, index + 1, item],
            itemStyle: {
                normal: {
                    color: getColor(item * 1)
                }
            }
        }
    });
    // 设置样式
    customChart.setOption({
        tooltip: {
            formatter: function (params) {
                return params.marker + ': ' + getText(params.value[3]);
            }
        },
        grid: {
            left: '2%',
            right: '2%',
            bottom: '30%',
            top: '0%'
        },
        yAxis: {
            show: false
        },
        xAxis: {
            max: customData.length,
            axisLabel: {
                formatter: function (value) {
                    if (value === 0) return '0%';
                    if (value === data.length) return '100%';
                    return `${parseInt((100 / data.length) * (value))}%`
                },
                showMaxLabel: true,
                showMinLabel: true
            },
            axisTick: {
                show: false
            },
            axisLine: {
                show: false
            },
        },
        series: [
            {
                type: 'custom',
                renderItem: renderItem,
                encode: {
                    x: [0, 1],
                    y: 0
                },
                data: customData
            }
        ]
    });
    customChart.on('click', function (params) {
        const dataIndex = params.dataIndex;
        const dataValue = params.data.value[3];
        if (dataValue < 0.8) {
            const range = document.createRange();
            const selection = window.getSelection();
            const referenceNode = document.querySelector(`#score_${dataIndex + 1}`);
            range.selectNodeContents(referenceNode);
            selection.removeAllRanges();
            selection.addRange(range)
            window.location.href = `#score_${dataIndex + 1}`;
        }
    });
}
// 切换显示AI内容
const initDomEvent = () => {
    // 切换按钮
    const radioDoms = document.querySelectorAll('.radio-customize');
    // 表格内容
    const tableDoms = document.querySelectorAll('.table-content');
    // 回到顶部
    const upDom = document.querySelector('.up-btn');
    // 循环遍历dom元素
    radioDoms.forEach((radioDom, index) => {
        radioDom.addEventListener('click', () => {
            // 记录当前显示下表
            aiContentIndex = index;
            // 移除所有元素的 'select' 类
            radioDoms.forEach((dom) => {
                dom.classList.remove('select');
            })
            // 循环操作表格隐藏
            tableDoms.forEach((dom) => {
                dom.classList.add('hidden');
            });
            // 显示当前内容
            tableDoms[index].classList.remove('hidden');
            // 为当前点击的元素添加 'select' 类
            radioDom.classList.add('select');
        })
    });
    // 点击回到顶部
    upDom.addEventListener('click', () => {
        window.scrollTo({
            top: 0, // 滚动到顶部
            behavior: 'smooth' // 平滑滚动
        });
    })
}
// 页面挂载后
window.onload = () => {
    // 初始化饼图
    initEchartsPie();
    // 初始化自定义
    initEchartsCustom();
    // 初始化事件
    initDomEvent();
}
