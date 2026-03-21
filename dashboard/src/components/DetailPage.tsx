import ActiveDevicesPanel from './ActiveDevicesPanel';
import SensorDetailPanel from './SensorDetailPanel';
import AudioPanel from './AudioPanel';
import RobotInfoPanel from './RobotInfoPanel';
import TestPanel from './TestPanel';
import type { ClientMessage } from '../types/ros';

interface DetailPageProps {
  sendAudioPlay: (soundKey: string) => void;
  sendAudioVolume: (volumePercent: number) => void;
  send: (msg: ClientMessage) => void;
}

export default function DetailPage({ sendAudioPlay, sendAudioVolume, send }: DetailPageProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 max-w-6xl mx-auto">
        <ActiveDevicesPanel />
        <SensorDetailPanel />
        <AudioPanel sendAudioPlay={sendAudioPlay} sendAudioVolume={sendAudioVolume} />
        <RobotInfoPanel />
        <TestPanel send={send} />
      </div>
    </div>
  );
}
