import { describe, expect, test } from 'vitest';
import * as ahooks from '.';
describe('ahooks', function () {
    test('exports modules should be defined', function () {
        Object.keys(ahooks).forEach(function (module) {
            expect(ahooks[module]).toBeDefined();
        });
    });
});
