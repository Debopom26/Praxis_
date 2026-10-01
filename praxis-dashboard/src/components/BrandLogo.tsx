import { useColorMode } from '../state/colorMode';

export function BrandLogo() {
  const { darkMode } = useColorMode();
  return <img src={darkMode ? '/assets/praxis-logo-transparent.png' : '/assets/praxis-logo-shadow.png'} alt="Praxis" />;
}
