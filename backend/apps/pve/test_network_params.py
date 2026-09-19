"""
网络创建参数映射自检。

不依赖 Django/DB/PVE，直接跑：
    python3 backend/apps/pve/test_network_params.py

校验 PVEServerViewSet 对 POST /nodes/{node}/network 的参数处理：
白名单过滤、布尔转 1/0、整数强转、未知字段丢弃。
"""


# 与 views.PVEServerViewSet 中的常量保持一致（此处独立复制以免引入 Django 依赖）
STR_PARAMS = {
    'iface', 'type', 'address', 'address6', 'cidr', 'cidr6',
    'gateway', 'gateway6', 'netmask', 'comments', 'comments6',
    'bridge_ports', 'bridge_vids', 'slaves', 'bond_mode',
    'bond_xmit_hash_policy', 'bond-primary', 'vlan-raw-device',
}
INT_PARAMS = {'mtu', 'vlan-id', 'netmask6'}
BOOL_PARAMS = {'autostart', 'bridge_vlan_aware'}


def build_params(data):
    """与 views.PVEServerViewSet._build_network_params 等价。"""
    params = {}
    for key, value in data.items():
        if key == 'delete':
            if isinstance(value, (list, tuple, set)):
                fields = list(value)
            else:
                fields = [f.strip() for f in str(value).split(',')]
            allowed = (STR_PARAMS | INT_PARAMS | BOOL_PARAMS) - {'iface', 'type'}
            fields = [f for f in fields if f in allowed]
            if fields:
                params['delete'] = ','.join(fields)
            continue
        if value is None or value == '':
            continue
        if key in BOOL_PARAMS:
            params[key] = 1 if value in (True, 1, '1', 'true', 'True') else 0
        elif key in INT_PARAMS:
            try:
                params[key] = int(value)
            except (TypeError, ValueError):
                raise ValueError(f'参数 {key} 必须是整数，收到: {value!r}')
        elif key in STR_PARAMS:
            params[key] = str(value).strip()
    return params


def test_bridge():
    out = build_params({
        'iface': ' vmbr2 ', 'type': 'bridge', 'autostart': True,
        'cidr': '192.168.1.10/24', 'gateway': '192.168.1.1',
        'bridge_vlan_aware': False, 'bridge_ports': 'eno1 eno2',
        'mtu': '1500', 'comments': '测试网桥',
    })
    assert out['iface'] == 'vmbr2', '应去掉首尾空格'
    assert out['autostart'] == 1, '布尔应转成 1'
    assert out['bridge_vlan_aware'] == 0, 'False 应转成 0'
    assert out['mtu'] == 1500 and isinstance(out['mtu'], int), 'mtu 应为 int'
    assert out['bridge_ports'] == 'eno1 eno2'


def test_bond():
    out = build_params({
        'iface': 'bond0', 'type': 'bond', 'slaves': 'eno1 eno2',
        'bond_mode': 'active-backup', 'bond-primary': 'eno1',
        'autostart': 'true',
    })
    assert out['slaves'] == 'eno1 eno2'
    assert out['bond-primary'] == 'eno1', '带连字符的键必须保留原名'
    assert out['autostart'] == 1, "字符串 'true' 应转成 1"


def test_vlan():
    out = build_params({
        'iface': 'vlan0', 'type': 'vlan',
        'vlan-raw-device': 'eno1', 'vlan-id': '100',
    })
    assert out['vlan-id'] == 100 and isinstance(out['vlan-id'], int)
    assert out['vlan-raw-device'] == 'eno1'


def test_rejects_unknown_and_empty():
    out = build_params({
        'iface': 'vmbr9', 'type': 'bridge',
        'cidr': '',                  # 空串丢弃
        'gateway': None,             # None 丢弃
        'rm': '-rf /',               # 未知字段丢弃
        'ovs_options': 'x',          # 不在白名单（当前只支持 linux 三类）
    })
    assert out == {'iface': 'vmbr9', 'type': 'bridge'}, f'意外放行了字段: {out}'


def test_delete_list_is_joined():
    """清空字段必须显式声明，PVE 不会因为字段缺省就清值。"""
    out = build_params({
        'iface': 'vmbr2', 'type': 'bridge',
        'delete': ['gateway', 'comments'],
    })
    assert out['delete'] == 'gateway,comments', f'实际: {out.get("delete")!r}'


def test_delete_accepts_comma_string():
    out = build_params({'type': 'bridge', 'delete': 'gateway, mtu'})
    assert out['delete'] == 'gateway,mtu', '逗号分隔字符串也应支持且去空格'


def test_delete_filters_unknown_and_identity_fields():
    out = build_params({
        'type': 'bridge',
        'delete': ['gateway', 'iface', 'type', 'rm -rf', 'ovs_options'],
    })
    # iface/type 是身份字段不可删；未知字段与非白名单字段一律丢弃
    assert out['delete'] == 'gateway', f'实际: {out.get("delete")!r}'


def test_delete_omitted_when_nothing_valid():
    out = build_params({'type': 'bridge', 'delete': ['nope']})
    assert 'delete' not in out, '过滤后为空时不应发送 delete 参数'


def test_int_param_rejects_garbage():
    try:
        build_params({'type': 'bridge', 'mtu': 'abc'})
    except ValueError as e:
        assert 'mtu' in str(e)
    else:
        raise AssertionError('非法整数应抛 ValueError')


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
            print(f'✅ {name}')
    print('全部通过')
