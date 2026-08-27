import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  AppShell,
  CapacityFailurePanel,
  ChoiceGroup,
  DetailsDisclosure,
  EngineeringAssessment,
  Field,
  HandoffPanel,
  InputWithUnit,
  PageHeader,
  ReadinessBar,
  ResultHero,
  StaleResultBanner,
} from './primitives';
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

  it('associates Field labels, hints, and errors with the composed control', () => {
    render(
      <I18nProvider>
        <Field id="speed" label="Speed" required hint="Use the posted speed" error="Speed is required">
          {(controlProps) => <InputWithUnit unit="km/h" {...controlProps} />}
        </Field>
      </I18nProvider>,
    );

    const input = screen.getByLabelText(/Speed/);
    expect(input).toHaveAttribute('id', 'speed');
    expect(input).toHaveAttribute('aria-describedby', 'speed-hint speed-error');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-required', 'true');
    expect(input).toBeRequired();
    expect(screen.getByText('Use the posted speed')).toHaveAttribute('id', 'speed-hint');
    expect(screen.getByText('Speed is required')).toHaveAttribute('id', 'speed-error');
    expect(screen.getByText('Required')).toBeInTheDocument();
  });

  it('uses the catalog for shared state and assessment text when the language changes', () => {
    render(
      <I18nProvider>
        <AppShell activePage="home" onNavigate={() => undefined} apiConnected>
          <ReadinessBar ready />
          <EngineeringAssessment items={['Evidence']} />
          <StaleResultBanner />
          <CapacityFailurePanel />
          <HandoffPanel />
        </AppShell>
      </I18nProvider>,
    );

    expect(screen.getByRole('link', { name: 'Skip to main content' })).toBeInTheDocument();
    expect(screen.getByText('✓ Ready to calculate')).toBeInTheDocument();
    expect(screen.getByText('ENGINEERING ASSESSMENT')).toBeInTheDocument();
    expect(screen.getByText('Input changed — recalculation required')).toBeInTheDocument();
    expect(screen.getByText('Capacity exceeded')).toBeInTheDocument();
    expect(screen.getByText('HCM method handoff')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Thai' }));

    expect(screen.getByRole('link', { name: 'ข้ามไปยังเนื้อหาหลัก' })).toBeInTheDocument();
    expect(screen.getByText('✓ พร้อมคำนวณ')).toBeInTheDocument();
    expect(screen.getByText('การประเมินทางวิศวกรรม')).toBeInTheDocument();
    expect(screen.getByText('ข้อมูลเปลี่ยนแปลง — ต้องคำนวณใหม่')).toBeInTheDocument();
    expect(screen.getByText('เกินความจุ')).toBeInTheDocument();
    expect(screen.getByText('การส่งต่อไปยังวิธี HCM')).toBeInTheDocument();
  });
});
