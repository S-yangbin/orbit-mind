import { useState, useEffect } from "react";
import { Button, message, Tooltip, Space } from "antd";
import { ScanOutlined } from "@ant-design/icons";
import { triggerScan, getScanStatus } from "../api/scan";

interface Props {
  onScanComplete?: () => void;
}

export function ScanButton({ onScanComplete }: Props) {
  const [scanning, setScanning] = useState(false);
  const [lastResult, setLastResult] = useState<string>("");
  const [lastScanAt, setLastScanAt] = useState<string>("");

  // Poll scan status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await getScanStatus();
        setScanning(status.is_running);
        if (status.last_result) setLastResult(status.last_result);
        if (status.last_scan_at) setLastScanAt(status.last_scan_at);
        if (scanning && !status.is_running && onScanComplete) {
          onScanComplete();
          message.success("扫描完成");
        }
      } catch {
        // ignore
      }
    };
    checkStatus();
    const timer = setInterval(checkStatus, 3000);
    return () => clearInterval(timer);
  }, [scanning, onScanComplete]);

  const handleScan = async () => {
    try {
      const result = await triggerScan();
      message.info(result.message);
      setScanning(true);
    } catch {
      message.error("扫描触发失败");
    }
  };

  return (
    <Tooltip title={lastResult || (lastScanAt ? `上次扫描: ${lastScanAt}` : "未扫描过")}>
      <Button
        icon={<ScanOutlined />}
        loading={scanning}
        onClick={handleScan}
        disabled={scanning}
      >
        {scanning ? "扫描中..." : "触发扫描"}
      </Button>
    </Tooltip>
  );
}
