"""
PVE termproxy 线协议分帧自检。

不依赖 Django/PVE，直接跑：
    python3 backend/apps/pve/test_termproxy_framing.py

协议取自官方 pve-xtermjs (src/www/main.js)：
    握手   <user>:<vncticket>\\n      成功后服务端回 "OK"
    输入   0:<UTF-8 字节长度>:<data>
    改窗口 1:<cols>:<rows>:
    保活   2
长度是 **UTF-8 字节数** 而非字符数 —— 中文输入写错这里会让 PVE 截断或挂起。
"""


def frame_input(data: str) -> str:
    """与 NodeShellConsumer.receive 中 input 分支等价。"""
    return f'0:{len(data.encode("utf-8"))}:{data}'


def frame_resize(cols, rows) -> str:
    """与 NodeShellConsumer.receive 中 resize 分支等价。"""
    return f'1:{int(cols)}:{int(rows)}:'


def frame_handshake(user: str, ticket: str) -> str:
    return f'{user}:{ticket}\n'


def test_ascii_input_length():
    assert frame_input('ls -al\r') == '0:7:ls -al\r'


def test_utf8_length_counts_bytes_not_chars():
    # 3 个汉字 = 9 字节，若按字符数会发成 0:3: 导致 PVE 截断
    assert frame_input('你好啊') == '0:9:你好啊'


def test_mixed_width_input():
    data = 'echo 中文'
    assert frame_input(data) == f'0:{len(data.encode("utf-8"))}:{data}'
    assert frame_input(data).startswith('0:11:')


def test_empty_input():
    assert frame_input('') == '0:0:'


def test_control_chars():
    # Ctrl+C
    assert frame_input('\x03') == '0:1:\x03'


def test_resize_format_has_trailing_colon():
    assert frame_resize(120, 40) == '1:120:40:'


def test_resize_coerces_str_numbers():
    assert frame_resize('80', '24') == '1:80:24:'


def test_handshake_format():
    assert frame_handshake('root@pam', 'PVEVNC:ABC') == 'root@pam:PVEVNC:ABC\n'


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
            print(f'✅ {name}')
    print('全部通过')
