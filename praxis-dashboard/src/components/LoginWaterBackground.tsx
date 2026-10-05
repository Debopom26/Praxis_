import { ElementsBackground as ElementsCollection } from '../shaders/elements/ElementsBackground';
import '../shaders/threeui.css';

export default function LoginWaterBackground() {
  return (
    <div className="shader-frame login-water-background" aria-hidden="true">
      <ElementsCollection
        variant="water"
        speed={0.58}
        size={0.85}
        particleAmount={0.61}
        hue={0}
        saturation={1.00}
        brightness={1.00}
        opacity={1.00}
      />
    </div>
  );
}
