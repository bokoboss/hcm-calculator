import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import {
  AppShell,
  AppHeader,
  CapacityFailurePanel,
  ChoiceGroup,
  DetailsDisclosure,
  EngineeringAssessment,
  ErrorSummary,
  Field,
  FixedCondition,
  HandoffPanel,
  InputWithUnit,
  PageHeader,
  ReadinessBar,
  ResultHero,
  StatusBar,
  StaleResultPanel,
  WarningPanel,
  runtimeStatusKey,
} from './primitives';
import { I18nProvider } from '../i18n';

describe('R0 shared design-system primitives', () => {
  it('presents a fixed method condition as text and exposes a keyboard recovery action only on error', () => {
    const onRecover = vi.fn();
    const { rerender } = render(<FixedCondition id="fixed-control" label="Downstream boundary control" value="Signalized" description="Fixed by current qualified method" recoveryLabel="Use required value: Signalized" onRecover={onRecover} />);
    expect(screen.getByRole('group', { name: 'Downstream boundary control' })).toBeVisible();
    expect(screen.getByRole('status')).toHaveTextContent('Fixed by current qualified method');
    expect(screen.queryByRole('radio')).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    rerender(<FixedCondition id="fixed-control" label="Downstream boundary control" value="Signalized" invalidValue="Required value: Signalized" description="Fixed by current qualified method" error="The qualified downstream boundary must be signalized." recoveryLabel="Use required value: Signalized" onRecover={onRecover} />);
    const invalidGroup = screen.getByRole('group', { name: 'Downstream boundary control' });
    expect(invalidGroup).toHaveAttribute('aria-invalid', 'true');
    expect(invalidGroup).toHaveAttribute('aria-describedby', 'fixed-control-value fixed-control-error');
    expect(within(invalidGroup).getByText('Required value: Signalized')).toBeVisible();
    expect(within(invalidGroup).queryByRole('status')).not.toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('must be signalized');
    const recovery = screen.getByRole('button', { name: 'Use required value: Signalized' });
    recovery.focus();
    expect(recovery).toHaveFocus();
    fireEvent.click(recovery);
    expect(onRecover).toHaveBeenCalledOnce();
  });

  it('keeps the required fixed value localized when invalid and restores the ordinary value when valid', () => {
    const { rerender } = render(<FixedCondition id="fixed-control" label="Downstream boundary control" value="Signalized" invalidValue="Required value: Signalized" description="Fixed by current qualified method" error="The qualified downstream boundary must be signalized." recoveryLabel="Use required value: Signalized" onRecover={() => undefined} />);
    expect(screen.getByText('Required value: Signalized')).toBeVisible();
    rerender(<FixedCondition id="fixed-control" label="การควบคุมที่ทางแยกปลายทาง" value="สัญญาณไฟ" invalidValue="ค่าที่วิธีกำหนด: สัญญาณไฟ" description="กำหนดโดยขอบเขตของวิธีที่ผ่านการรับรอง" error="ขอบเขตปลายทางต้องควบคุมด้วยสัญญาณไฟ" recoveryLabel="ใช้ค่าที่วิธีกำหนด: สัญญาณไฟ" onRecover={() => undefined} />);
    expect(screen.getByText('ค่าที่วิธีกำหนด: สัญญาณไฟ')).toBeVisible();
    rerender(<FixedCondition id="fixed-control" label="Downstream boundary control" value="Signalized" invalidValue="Required value: Signalized" description="Fixed by current qualified method" recoveryLabel="Use required value: Signalized" onRecover={() => undefined} />);
    expect(screen.getByText('Signalized', { exact: true })).toBeVisible();
    expect(screen.getByRole('status')).toHaveTextContent('Fixed by current qualified method');
  });

  it('classifies runtime hosts without build-time configuration', () => {
    expect(runtimeStatusKey('localhost')).toBe('status.local_runtime');
    expect(runtimeStatusKey('127.0.0.1')).toBe('status.local_runtime');
    expect(runtimeStatusKey('127.0.0.2')).toBe('status.local_runtime');
    expect(runtimeStatusKey('127.255.255.254')).toBe('status.local_runtime');
    expect(runtimeStatusKey('127.example.com')).toBe('status.hosted_runtime');
    expect(runtimeStatusKey('128.0.0.1')).toBe('status.hosted_runtime');
    expect(runtimeStatusKey('::1')).toBe('status.local_runtime');
    expect(runtimeStatusKey('hcm-calculator-bice.vercel.app')).toBe('status.vercel_runtime');
    expect(runtimeStatusKey('example.company.com')).toBe('status.hosted_runtime');
  });

  it('renders the hostname-derived runtime label in both locales', () => {
    window.localStorage.clear();
    render(<I18nProvider><AppHeader /><StatusBar apiConnected hostname="hcm-calculator-bice.vercel.app" /></I18nProvider>);

    expect(screen.getByText('Hosted / Vercel')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Thai' }));
    expect(screen.getByText('โฮสต์ / Vercel')).toBeInTheDocument();
    window.localStorage.clear();
  });

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
          <StaleResultPanel />
          <CapacityFailurePanel />
          <HandoffPanel />
          <WarningPanel message="Maximum desirable flow is exceeded." />
        </AppShell>
      </I18nProvider>,
    );

    expect(screen.getByRole('link', { name: 'Skip to main content' })).toBeInTheDocument();
    expect(screen.getByText('✓ Ready to calculate')).toBeInTheDocument();
    expect(screen.getByText('ENGINEERING ASSESSMENT')).toBeInTheDocument();
    expect(screen.getByText('Input changed — recalculation required')).toBeInTheDocument();
    expect(screen.getByText('Capacity exceeded')).toBeInTheDocument();
    expect(screen.getByText('HCM method handoff')).toBeInTheDocument();
    expect(screen.getByText('Current result with warning')).toBeInTheDocument();
    expect(screen.getByText('Maximum desirable flow is exceeded.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Thai' }));

    expect(screen.getByRole('link', { name: 'ข้ามไปยังเนื้อหาหลัก' })).toBeInTheDocument();
    expect(screen.getByText('✓ พร้อมคำนวณ')).toBeInTheDocument();
    expect(screen.getByText('การประเมินทางวิศวกรรม')).toBeInTheDocument();
    expect(screen.getByText('ข้อมูลเปลี่ยนแปลง — ต้องคำนวณใหม่')).toBeInTheDocument();
    expect(screen.getByText('เกินความจุ')).toBeInTheDocument();
    expect(screen.getByText('การส่งต่อไปยังวิธี HCM')).toBeInTheDocument();
    expect(screen.getByText('ผลลัพธ์ปัจจุบันพร้อมคำเตือน')).toBeInTheDocument();
  });

  it('keeps method navigation persistent and links validation recovery to a field', () => {
    render(
      <I18nProvider>
        <AppShell
          activePage="new-analysis"
          activeMethodId="weaving_segment"
          onNavigate={() => undefined}
          onSelectMethod={() => undefined}
          apiConnected
        >
          <input id="speed-field" />
          <ErrorSummary errors={[{ message: 'Speed is required', targetId: 'speed-field' }]} />
        </AppShell>
      </I18nProvider>,
    );

    for (const methodId of [
      'two_lane_segment',
      'two_lane_facility',
      'multilane_segment',
      'basic_freeway_segment',
      'weaving_segment',
      'merge_segment',
      'diverge_segment',
    ]) {
      expect(screen.getAllByTestId(`nav-method-${methodId}`)).toHaveLength(2);
    }
    expect(screen.getAllByTestId('nav-method-weaving_segment')[0]).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: 'Speed is required' })).toHaveAttribute('href', '#speed-field');
  });
});
