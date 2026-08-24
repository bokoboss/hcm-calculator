import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AppShell, ChoiceGroup, DetailsDisclosure, InputWithUnit, PageHeader, ResultHero } from './primitives';
import { I18nProvider } from '../i18n';

describe('R0 shared design-system primitives', () => {
  it('renders semantic shell landmarks and skip target', () => {
    render(<I18nProvider><AppShell activePage="home" onNavigate={() => undefined} apiConnected>{<PageHeader title="Home" />}</AppShell></I18nProvider>);
    expect(screen.getAllByRole('banner')).toHaveLength(2);
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content');
    expect(screen.getByRole('link', { name: 'Skip to main content' })).toHaveAttribute('href', '#main-content');
  });

  it('associates input units and supports accessible choice groups', () => {
    render(<><label htmlFor="speed">Speed</label><InputWithUnit id="speed" unit="km/h" /><ChoiceGroup legend="Source" name="source" options={[{ value: 'measured', label: 'Measured' }]} /></>);
    expect(screen.getByLabelText('Speed')).toHaveAttribute('id', 'speed');
    expect(screen.getByText('km/h')).toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'Source' })).toBeInTheDocument();
  });

  it('exposes result state and disclosure semantics', async () => {
    render(<><ResultHero label="Level of service" value="Foundation" /><DetailsDisclosure title="Details">Evidence</DetailsDisclosure></>);
    expect(screen.getByText('Foundation')).toBeInTheDocument();
    const trigger = screen.getByRole('button', { name: /Details/ });
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
  });
});
