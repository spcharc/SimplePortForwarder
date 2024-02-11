#!/usr/bin/env python3

# requires Python 3.8+

import asyncio
import socket

__version__ = '1.0.0'
__author__ = 'spcharc'

async def pipe_data(reader, writer):
    # pipes data from reader into writer

    while len(data := await reader.read(8192)):  # 8kb
        writer.write(data)
        await writer.drain()

    writer.close()
    await writer.wait_closed()


def handler_wrapper(dest_addr, dest_port):
    async def handler(reader, writer):
        try:
            reader2, writer2 = await asyncio.open_connection(dest_addr, dest_port)
        except socket.gaierror:
            print('Hostname is invalid:', dest_addr, ':', dest_port)
            writer.close()
            await writer.wait_closed()
            return
        except ConnectionRefusedError:
            print('Connection refused by', dest_addr, ':', dest_port)
            writer.close()
            await writer.wait_closed()
            return
        except Exception:
            print('Cannot connect to', dest_addr, ':', dest_port)
            writer.close()
            await writer.wait_closed()
            return
        print('Connected to', dest_addr, ':', dest_port)
        await asyncio.gather(pipe_data(reader2, writer),
                             pipe_data(reader, writer2),
                             return_exceptions=True)
    return handler

async def main(rules_list):
    forward_list = [asyncio.start_server(handler_wrapper(dest_addr, dest_port), addr, port) for addr, port, dest_addr, dest_port in rules_list]
    await asyncio.gather(* forward_list)


if __name__ == '__main__':
    rules = [
        ['0.0.0.0', 1080, 'localhost', 80]
    ]
    # define rules as: local addr, local port, remote addr (can be host name), remote port

    loop = asyncio.new_event_loop()
    loop.run_until_complete(main(rules))
    print('Port forward start, rules =', rules)
    loop.run_forever()
