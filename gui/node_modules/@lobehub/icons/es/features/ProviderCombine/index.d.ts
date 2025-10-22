/// <reference types="react" />
import { FlexboxProps } from 'react-layout-kit';
import { ModelProviderKey } from '../providerEnum';
export interface ProviderCombineProps extends Omit<FlexboxProps, 'children' | 'horizontal' | 'height' | 'width' | 'align' | 'justify'> {
    provider?: ModelProviderKey | string;
    size?: number;
    type?: 'mono' | 'color';
}
declare const ProviderCombine: import("react").NamedExoticComponent<ProviderCombineProps>;
export default ProviderCombine;
