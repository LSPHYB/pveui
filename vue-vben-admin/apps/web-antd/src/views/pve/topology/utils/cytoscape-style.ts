
// SVG icon URLs (imported as data URLs via Vite)
import bridgeIcon from '../icons/bridge.svg';
import interfaceIcon from '../icons/interface.svg';
import lxcIcon from '../icons/lxc.svg';
import pveNodeIcon from '../icons/pve-node.svg';
import storageIcon from '../icons/storage.svg';
import vmIcon from '../icons/vm.svg';

export const NODE_TYPES = {
  'pve-node': { label: 'PVE 节点', icon: pveNodeIcon, color: '#5470c6' },
  vm: { label: '虚拟机', icon: vmIcon, color: '#ee6666' },
  lxc: { label: '容器', icon: lxcIcon, color: '#73c0de' },
  bridge: { label: '网桥', icon: bridgeIcon, color: '#91cc75' },
  interface: { label: '网口', icon: interfaceIcon, color: '#fac858' },
  storage: { label: '存储', icon: storageIcon, color: '#722ed1' },
} as const;

export type NodeType = keyof typeof NODE_TYPES;

export const getStylesheet = (): any[] => [
  {
    selector: 'node',
    style: {
      width: 52,
      height: 52,
      'background-color': '#fff',
      'background-image': (ele: any) => {
        const type = ele.data('type') as NodeType;
        return NODE_TYPES[type]?.icon ?? pveNodeIcon;
      },
      'background-fit': 'contain',
      'background-clip': 'node',
      'background-opacity': 1,
      'border-width': 2,
      'border-color': (ele: any) => {
        const type = ele.data('type') as NodeType;
        return NODE_TYPES[type]?.color ?? '#999';
      },
      'border-style': 'solid',
      label: 'data(label)',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'font-size': 11,
      color: '#333',
      'text-margin-y': 4,
      'text-background-color': 'rgba(255,255,255,0.85)',
      'text-background-opacity': 1,
      'text-background-padding': '2px',
      'text-background-shape': 'roundrectangle',
      'text-wrap': 'wrap',
      'text-max-width': '90px',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#165dff',
      'background-color': '#e8f0ff',
    },
  },
  {
    selector: 'edge',
    style: {
      width: 2,
      'line-color': '#aaa',
      'target-arrow-color': '#aaa',
      'target-arrow-shape': 'none',
      'curve-style': 'bezier',
      label: 'data(label)',
      'font-size': 10,
      color: '#888',
      'text-background-color': '#fff',
      'text-background-opacity': 0.8,
      'text-background-padding': '2px',
    },
  },
  {
    selector: 'edge:selected',
    style: {
      'line-color': '#165dff',
      width: 3,
    },
  },
  // edgehandles 句柄 —— 必须清除继承来的 background-image，否则会渲染成节点图标大小
  {
    selector: '.eh-handle',
    style: {
      'background-color': '#165dff',
      'background-image': 'none',
      'border-width': 2,
      'border-color': '#fff',
      width: 12,
      height: 12,
      shape: 'ellipse',
      label: '',
      'overlay-opacity': 0,
      'z-index': 9999,
    },
  },
  {
    selector: '.eh-hover',
    style: {
      'background-color': '#e8f0ff',
      'border-color': '#165dff',
      'border-width': 2,
    },
  },
  {
    selector: '.eh-source',
    style: {
      'border-color': '#165dff',
      'border-width': 3,
    },
  },
  {
    selector: '.eh-target',
    style: {
      'border-color': '#00b42a',
      'border-width': 3,
    },
  },
  {
    selector: '.eh-preview, .eh-ghost-edge',
    style: {
      'line-color': '#165dff',
      'line-style': 'dashed',
      'target-arrow-color': '#165dff',
      'target-arrow-shape': 'triangle',
      opacity: 0.6,
    },
  },
  // dashed edge (for physical-interface connections in live mode)
  {
    selector: 'edge[style="dashed"]',
    style: {
      'line-style': 'dashed',
      'line-color': '#bbb',
    },
  },
];
