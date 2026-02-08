declare module '@novnc/novnc/core/rfb' {
  export default class RFB {
    background: string;
    clipViewport: boolean;
    compressionLevel: number;
    dragViewport: boolean;
    focusOnClick: boolean;
    qualityLevel: number;
    resizeSession: boolean;
    scaleViewport: boolean;
    viewOnly: boolean;
    constructor(
      target: HTMLElement,
      url: string,
      options?: {
        credentials?: { password?: string };
        repeaterID?: string;
        shared?: boolean;
      },
    );
    addEventListener(event: string, callback: (e: any) => void): void;
    disconnect(): void;
    removeEventListener(event: string, callback: (e: any) => void): void;
    sendCredentials(credentials: { password?: string }): void;
  }
}
