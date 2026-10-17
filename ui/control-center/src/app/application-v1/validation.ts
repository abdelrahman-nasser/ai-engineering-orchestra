/** UI-owned, transport-neutral validation. No Core imports or authority checks. */
export type Decoder<T> = (value: unknown) => T;
export type Value<D> = D extends Decoder<infer T> ? T : never;

export class ProjectionError extends Error {
  constructor() {
    super('Invalid application v1.0 projection; observation withheld.');
  }
}
export function requireValid(condition: unknown): asserts condition {
  if (!condition) throw new ProjectionError();
}
export function scalarText(value: unknown): string {
  requireValid(typeof value === 'string' && value.length > 0);
  // Reject unpaired UTF-16 surrogates without changing any opaque identifier.
  requireValid(
    !/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(value),
  );
  return value;
}
export function oneOf<const T extends readonly (string | number | boolean)[]>(
  ...values: T
): Decoder<T[number]> {
  return (value) => {
    requireValid(values.includes(value as T[number]));
    return value as T[number];
  };
}
export function nullable<T>(decode: Decoder<T>): Decoder<T | null> {
  return (value) => (value === null ? null : decode(value));
}
export function list<T>(decode: Decoder<T>): Decoder<readonly T[]> {
  return (value) => {
    requireValid(Array.isArray(value));
    return Object.freeze(value.map(decode));
  };
}
export function object<
  const S extends Record<string, Decoder<unknown>>,
  const O extends Record<string, Decoder<unknown>> = Record<never, never>,
>(
  shape: S,
  optionalShape: O = {} as O,
): Decoder<{ readonly [K in keyof S]: Value<S[K]> } & { readonly [K in keyof O]?: Value<O[K]> }> {
  return (value) => {
    requireValid(value !== null && typeof value === 'object' && !Array.isArray(value));
    requireValid(
      Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null,
    );
    const keys = Reflect.ownKeys(value);
    const expected = Object.keys(shape);
    const optional = Object.keys(optionalShape);
    requireValid(
      expected.every((key) => Object.hasOwn(value, key)) &&
        keys.every(
          (key) => typeof key === 'string' && (expected.includes(key) || optional.includes(key)),
        ),
    );
    const result: Record<string, unknown> = {};
    for (const key of expected) result[key] = shape[key]((value as Record<string, unknown>)[key]);
    for (const key of optional)
      if (Object.hasOwn(value, key))
        result[key] = optionalShape[key]((value as Record<string, unknown>)[key]);
    return Object.freeze(result) as {
      readonly [K in keyof S]: Value<S[K]>;
    } & { readonly [K in keyof O]?: Value<O[K]> };
  };
}

declare const decimalBrand: unique symbol;
export type Decimal = string & { readonly [decimalBrand]: true };
export function decimal(min = 0n, max?: bigint): Decoder<Decimal> {
  return (value) => {
    requireValid(typeof value === 'string' && /^(0|[1-9][0-9]*)$/.test(value));
    const exact = BigInt(value);
    requireValid(exact >= min && (max === undefined || exact <= max));
    return value as Decimal;
  };
}

/** Microseconds since 0001-01-01; never a Date/Number round trip. */
export function timeKey(text: string): bigint {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?Z$/.exec(text);
  requireValid(m);
  const [year, month, day, hour, minute, second] = m.slice(1, 7).map((part) => BigInt(part));
  const leap = year % 4n === 0n && (year % 100n !== 0n || year % 400n === 0n);
  const lengths = [31n, leap ? 29n : 28n, 31n, 30n, 31n, 30n, 31n, 31n, 30n, 31n, 30n, 31n];
  requireValid(
    year >= 1n &&
      month >= 1n &&
      month <= 12n &&
      day >= 1n &&
      hour <= 23n &&
      minute <= 59n &&
      second <= 59n,
  );
  let days = 365n * (year - 1n) + (year - 1n) / 4n - (year - 1n) / 100n + (year - 1n) / 400n;
  for (let index = 0; index < lengths.length; index++) {
    if (BigInt(index + 1) < month) days += lengths[index];
    if (BigInt(index + 1) === month) requireValid(day <= lengths[index]);
  }
  days += day - 1n;
  return (
    ((days * 24n + hour) * 3600n + minute * 60n + second) * 1000000n +
    BigInt((m[7] ?? '').padEnd(6, '0'))
  );
}
export const grantTime: Decoder<string> = (value) => {
  const text = scalarText(value);
  timeKey(text);
  return text;
};
export const utcTime: Decoder<string> = (value) => {
  const text = grantTime(value);
  requireValid(/\.\d{6}Z$/.test(text));
  return text;
};

/** Duplicate-aware JSON decoding. Numeric tokens are only the bounded small integers.
 * Lossless fields must be strings and are never parsed through JS Number. */
export function parseProjection(text: string): unknown {
  let index = 0;
  const whitespace = () => {
    while (/[\x20\x09\x0a\x0d]/.test(text[index] ?? 'x')) index++;
  };
  const string = (): string => {
    const start = index++;
    while (index < text.length) {
      const char = text[index++];
      if (char === '\\') index++;
      else if (char === '"') {
        try {
          return JSON.parse(text.slice(start, index)) as string;
        } catch {
          throw new ProjectionError();
        }
      }
    }
    throw new ProjectionError();
  };
  const read = (depth: number): unknown => {
    requireValid(depth <= 64);
    whitespace();
    const char = text[index];
    if (char === '"') return string();
    if (char === '{' || char === '[') {
      index++;
      const isObject = char === '{';
      const end = isObject ? '}' : ']';
      const result: Record<string, unknown> = Object.create(null);
      const items: unknown[] = [];
      whitespace();
      if (text[index] === end) {
        index++;
        return isObject ? result : items;
      }
      while (index < text.length) {
        whitespace();
        let key = '';
        if (isObject) {
          requireValid(text[index] === '"');
          key = string();
          whitespace();
          requireValid(!Object.hasOwn(result, key) && text[index++] === ':');
        }
        const value = read(depth + 1);
        if (isObject) result[key] = value;
        else items.push(value);
        whitespace();
        if (text[index] === end) {
          index++;
          return isObject ? result : items;
        }
        requireValid(text[index++] === ',');
      }
      throw new ProjectionError();
    }
    for (const [token, value] of [
      ['true', true],
      ['false', false],
      ['null', null],
    ] as const) {
      if (text.startsWith(token, index)) {
        index += token.length;
        return value;
      }
    }
    const token = /^(0|[1-9][0-9]*)/.exec(text.slice(index))?.[0];
    requireValid(token && token.length <= 3 && BigInt(token) <= 100n);
    index += token.length;
    return Number(token); // Only bounded exact small integers reach this conversion.
  };
  const value = read(0);
  whitespace();
  requireValid(index === text.length);
  return value;
}
