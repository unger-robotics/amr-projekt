import ActiveDevicesPanel from './ActiveDevicesPanel';
import SensorDetailPanel from './SensorDetailPanel';
import AudioPanel from './AudioPanel';
import RobotInfoPanel from './RobotInfoPanel';

interface DetailPageProps {
  sendAudioPlay: (soundKey: string) => void;
  sendAudioVolume: (volumePercent: number) => void;
}

export default function DetailPage({ sendAudioPlay, sendAudioVolume }: DetailPageProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 max-w-6xl mx-auto">
        <ActiveDevicesPanel />
        <SensorDetailPanel />
        <AudioPanel sendAudioPlay={sendAudioPlay} sendAudioVolume={sendAudioVolume} />
        <RobotInfoPanel />
      </div>
    </div>
  );
}
