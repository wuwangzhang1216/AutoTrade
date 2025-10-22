import { FC } from 'react';
import { FlexboxProps } from 'react-layout-kit';
export interface CalloutProps extends FlexboxProps {
    type?: 'tip' | 'error' | 'important' | 'info' | 'warning';
}
declare const Callout: FC<CalloutProps>;
export default Callout;
