import type { ElementDefinition } from 'cytoscape';

/**
 * 将 PVE 实时 API 数据转换为 Cytoscape elements
 */
export function pveDataToCytoscape(params: {
  nodeName: string;
  networks: any[];
  vmConfigs: Array<{ vmid: number; name: string; config: any } | null>;
  lxcConfigs: Array<{ vmid: number; name: string; config: any } | null>;
}): ElementDefinition[] {
  const { nodeName, networks, vmConfigs, lxcConfigs } = params;
  const elements: ElementDefinition[] = [];
  const nodeIds = new Set<string>();

  const addNode = (node: ElementDefinition) => {
    const id = node.data.id as string;
    if (!nodeIds.has(id)) {
      nodeIds.add(id);
      elements.push(node);
    }
  };

  // PVE 宿主节点
  addNode({
    data: { id: nodeName, label: nodeName, type: 'pve-node' },
  });

  // 解析 net* 配置找 bridge 名
  const findBridges = (config: any): string[] => {
    const found: string[] = [];
    for (const key in config) {
      if (key.startsWith('net')) {
        const match = config[key]?.match?.(/bridge=([\w-]+)/);
        if (match?.[1]) found.push(match[1]);
      }
    }
    return found;
  };

  // 从 QEMU ipconfig* 字段提取 IP（cloud-init 专用）
  const extractVmIps = (config: any): string[] => {
    const ips: string[] = [];
    for (const key in config) {
      if (key.startsWith('ipconfig')) {
        const match = config[key]?.match?.(/ip=([\d.]+(?:\/\d+)?)/);
        if (match?.[1]) ips.push(match[1]);
      }
    }
    return ips;
  };

  // 从 QEMU net* 提取网卡信息 [{ mac, bridge }]
  const extractVmNics = (config: any): Array<{ mac: string; bridge: string }> => {
    const nics: Array<{ mac: string; bridge: string }> = [];
    for (const key in config) {
      if (key.startsWith('net')) {
        const val: string = config[key] ?? '';
        const macMatch = val.match(/(?:virtio|e1000|rtl8139|vmxnet3)=([0-9A-Fa-f:]{17})/);
        const brMatch = val.match(/bridge=([\w-]+)/);
        if (macMatch?.[1]) {
          nics.push({ mac: macMatch[1], bridge: brMatch?.[1] ?? '' });
        }
      }
    }
    return nics;
  };

  // 从 LXC net* 字段提取 IP（如 net0: name=eth0,bridge=vmbr0,ip=192.168.1.1/24）
  const extractLxcIps = (config: any): string[] => {
    const ips: string[] = [];
    for (const key in config) {
      if (key.startsWith('net')) {
        const match = config[key]?.match?.(/ip=([\d.]+(?:\/\d+)?)/);
        if (match?.[1] && match[1] !== 'dhcp') ips.push(match[1]);
      }
    }
    return ips;
  };

  // 处理网络接口
  networks.forEach((net) => {
    if (net.type === 'bridge') {
      // PVE 返回 cidr（如 192.168.1.1/24）或 address（纯 IP）
      const bridgeIp = net.cidr || net.address || '';
      addNode({
        data: {
          id: net.iface,
          label: bridgeIp ? `${net.iface}\n${bridgeIp}` : net.iface,
          type: 'bridge',
          ip: bridgeIp,
        },
      });
      // bridge → pve-node
      elements.push({
        data: { source: net.iface, target: nodeName, label: '' },
      });

      // bridge ports (物理网口)
      if (net.bridge_ports) {
        net.bridge_ports.split(/\s+/).forEach((port: string) => {
          addNode({
            data: { id: port, label: port, type: 'interface' },
          });
          elements.push({
            data: { source: port, target: net.iface, label: '' },
          });
        });
      }
    } else if (net.active && net.iface) {
      addNode({
        data: { id: net.iface, label: net.iface, type: 'interface' },
      });
      elements.push({
        data: { source: net.iface, target: nodeName, label: '', style: 'dashed' },
      });
    }
  });

  // 虚拟机
  vmConfigs.forEach((vm) => {
    if (!vm) return;
    const id = `vm-${vm.vmid}`;
    const ip = extractVmIps(vm.config).join(', '); // cloud-init 才有，否则为空
    const nics = extractVmNics(vm.config);
    addNode({
      data: {
        id,
        label: `VM ${vm.vmid}\n${vm.name}`,
        type: 'vm',
        vmid: vm.vmid,
        ip,
        nics, // [{ mac, bridge }, ...]
      },
    });
    findBridges(vm.config).forEach((br) => {
      addNode({
        data: { id: br, label: br, type: 'bridge' },
      });
      elements.push({ data: { source: id, target: br, label: '' } });
    });
  });

  // 容器
  lxcConfigs.forEach((lxc) => {
    if (!lxc) return;
    const id = `lxc-${lxc.vmid}`;
    const ips = extractLxcIps(lxc.config);
    addNode({
      data: {
        id,
        label: `LXC ${lxc.vmid}\n${lxc.name}`,
        type: 'lxc',
        vmid: lxc.vmid,
        ip: ips.join(', '),
      },
    });
    findBridges(lxc.config).forEach((br) => {
      addNode({
        data: { id: br, label: br, type: 'bridge' },
      });
      elements.push({ data: { source: id, target: br, label: '' } });
    });
  });

  return elements;
}

/**
 * 将 Cytoscape elements 序列化为后端存储格式
 */
export function serializeCytoscapeData(cy: any) {
  return cy.json().elements;
}

/**
 * 从后端 diagram_data 还原 Cytoscape elements
 */
export function deserializeCytoscapeData(diagramData: any): ElementDefinition[] {
  if (!diagramData) return [];
  // 支持两种格式: { nodes, edges } 或 { elements: { nodes, edges } }
  if (diagramData.elements) {
    const { nodes = [], edges = [] } = diagramData.elements;
    return [...nodes, ...edges];
  }
  if (diagramData.nodes || diagramData.edges) {
    return [...(diagramData.nodes ?? []), ...(diagramData.edges ?? [])];
  }
  return [];
}
