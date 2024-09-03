# TODO

# @parametrize_byteorder
# def test_pack_unpack(byteorder: str) -> None:
#     @dcs.dataclass(byteorder)
#     class Test:
#         a: dcs.U8
#         b: dcs.U16
#         c: dcs.U32
#         d: dcs.U64

#         e: dcs.I8
#         f: dcs.I16
#         g: dcs.I32
#         h: dcs.I64

#         j: bool
#         k: bytes

#         m: dcs.F32
#         n: dcs.F64

#         o: Annotated[bytes, 3]
#         p: Annotated[bytes, dcs.BytesField(5)]

#     t = Test(
#         a=0xff,
#         b=0xffff,
#         c=0xffff_ffff,
#         d=0xffff_ffff_ffff_ffff,
#         e=-0x80,
#         f=-0x8000,
#         g=-0x8000_0000,
#         h=-0x8000_0000_0000_0000,
#         j=True,
#         k=b'x',
#         m=0.25,
#         n=PI,
#         o=b'123',
#         p=b'12345',
#     )

#     fmt = byteorder + 'BHIQ bhiq ?c fd 3s5s'
#     assert dcs.get_struct_size(Test) == struct.calcsize(fmt)
#     assert dcs.get_struct_size(t) == struct.calcsize(fmt)

#     packed = t.pack()
#     assert isinstance(packed, bytes)

#     unpacked = Test.from_packed(packed)
#     assert isinstance(unpacked, Test)

#     assert t == unpacked


# def test_pack_unpack_native_types() -> None:
#     @dcs.dataclass()
#     class Test:
#         size: dcs.UnsignedSize
#         ssize: dcs.SignedSize
#         pointer: dcs.Pointer

#     t = Test(10, -10, 100)
#     packed = t.pack()
#     unpacked = Test.from_packed(packed)
#     assert t == unpacked


# @parametrize_byteorder
# def test_packed_bytes_padding(byteorder: str) -> None:
#     @dcs.dataclass(byteorder)
#     class Test:
#         x: Annotated[bytes, 5]

#     assert dcs.get_struct_size(Test) == struct.calcsize(byteorder + '5s')

#     t = Test(b'').pack()
#     assert t == b'\x00' * 5
#     assert Test.from_packed(t) == Test(b'\x00' * 5)

#     t = Test(b'123').pack()
#     assert t == b'123\x00\x00'
#     assert Test.from_packed(t) == Test(b'123\x00\x00')


# @parametrize_byteorder
# def test_pack_unpack_empty(byteorder: str) -> None:
#     @dcs.dataclass(byteorder)
#     class Empty:
#         pass

#     assert dcs.get_struct_size(Empty) == 0

#     assert Empty().pack() == b''
#     assert Empty.from_packed(b'') == Empty()
