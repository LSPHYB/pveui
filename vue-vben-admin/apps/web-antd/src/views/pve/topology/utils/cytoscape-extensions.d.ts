declare module 'cytoscape-cxtmenu' {
  import type { Core } from 'cytoscape';
  const CxtMenu: (cy: Core) => void;
  export default CxtMenu;
}

declare module 'cytoscape-edgehandles' {
  import type { Core } from 'cytoscape';
  const EdgeHandles: (cy: Core) => void;
  export default EdgeHandles;
}
